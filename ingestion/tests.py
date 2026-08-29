from pathlib import Path

from django.test import SimpleTestCase

from .parser import parse_alert_email

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class ParseAlertEmailTests(SimpleTestCase):
    """Validated against a real Upwork 'New job alert' email fetched from
    a live inbox (2026-08-29): 'Paid Smartphone Project | Earn Up to $400'."""

    def setUp(self):
        self.html = (FIXTURES_DIR / "sample_alert_email.html").read_text()

    def test_extracts_single_job(self):
        jobs = parse_alert_email(self.html)
        self.assertEqual(len(jobs), 1)

    def test_extracts_title(self):
        [job] = parse_alert_email(self.html)
        self.assertEqual(job.title, "📱 Paid Smartphone Project | Earn Up to $400")

    def test_extracts_job_uid(self):
        [job] = parse_alert_email(self.html)
        self.assertEqual(job.job_uid, "~022093619701101896117")

    def test_extracts_canonical_url_from_view_details_button(self):
        [job] = parse_alert_email(self.html)
        self.assertTrue(job.url.startswith("https://www.upwork.com/jobs/~022093619701101896117"))
        self.assertNotIn("link=", job.url)

    def test_extracts_snippet_without_trailing_more_label(self):
        [job] = parse_alert_email(self.html)
        self.assertIn("We’re looking for people with compatible smartphones", job.snippet)
        self.assertIn("You don’t need to be a professional creator", job.snippet)
        self.assertFalse(job.snippet.endswith("more"))

    def test_empty_html_returns_no_jobs(self):
        self.assertEqual(parse_alert_email(""), [])

    def test_html_with_no_job_links_returns_no_jobs(self):
        self.assertEqual(parse_alert_email("<html><body>No jobs here</body></html>"), [])
