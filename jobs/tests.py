from django.test import SimpleTestCase

from .models import Job
from .services.classification import classify
from .utils import extract_job_uid


class ClassifyTests(SimpleTestCase):
    def test_real_upwork_snippet_is_unknown(self):
        """Real Upwork alert snippets are short and rarely mention team
        size — classify() should default to unknown rather than guessing."""
        snippet = (
            "We’re looking for people with compatible smartphones to join a paid "
            "video recording project. You don’t need to be a professional creator…"
        )
        freelancer_type, meta = classify(snippet)
        self.assertEqual(freelancer_type, Job.FreelancerType.UNKNOWN)
        self.assertEqual(meta["multiple_hits"], [])
        self.assertEqual(meta["single_hits"], [])

    def test_detects_multiple_freelancers(self):
        freelancer_type, _ = classify("We are hiring multiple freelancers for this project.")
        self.assertEqual(freelancer_type, Job.FreelancerType.MULTIPLE)

    def test_detects_single_freelancer(self):
        freelancer_type, _ = classify("Looking for a freelancer to build a landing page.")
        self.assertEqual(freelancer_type, Job.FreelancerType.SINGLE)

    def test_empty_text_is_unknown(self):
        freelancer_type, _ = classify("")
        self.assertEqual(freelancer_type, Job.FreelancerType.UNKNOWN)


class ExtractJobUidTests(SimpleTestCase):
    def test_extracts_uid_from_real_alert_url(self):
        url = (
            "https://www.upwork.com/jobs/~022093619701101896117"
            "?frkscc=L8I5uCFM3sUB"
        )
        self.assertEqual(extract_job_uid(url), "~022093619701101896117")

    def test_extracts_uid_with_title_slug(self):
        url = "https://www.upwork.com/jobs/Paid-Smartphone-Project_~022093619701101896117/"
        self.assertEqual(extract_job_uid(url), "~022093619701101896117")

    def test_no_uid_returns_none(self):
        self.assertIsNone(extract_job_uid("https://www.upwork.com/nx/search/jobs/"))
