from django.test import SimpleTestCase

from .models import Job
from .services.classification import classify
from .utils import extract_job_uid


class ClassifyTests(SimpleTestCase):
    def test_real_upwork_snippet_now_matches_people_as_multiple(self):
        """This is the actual 'Paid Smartphone Project' snippet — it was
        UNKNOWN before 'people' was added to MULTIPLE_PATTERNS, and is a
        known false positive now (it's really a single-hire job; 'looking
        for people' is just recruiting phrasing). Documented trade-off,
        not a bug: the user explicitly asked for 'people' as a signal."""
        snippet = (
            "We’re looking for people with compatible smartphones to join a paid "
            "video recording project. You don’t need to be a professional creator…"
        )
        freelancer_type, meta = classify(snippet)
        self.assertEqual(freelancer_type, Job.FreelancerType.MULTIPLE)
        self.assertEqual(meta["multiple_hits"], [r"\bpeople\b"])

    def test_detects_multiple_freelancers(self):
        freelancer_type, _ = classify("We are hiring multiple freelancers for this project.")
        self.assertEqual(freelancer_type, Job.FreelancerType.MULTIPLE)

    def test_detects_multiple_testers(self):
        freelancer_type, _ = classify("Need testers for our new mobile app.")
        self.assertEqual(freelancer_type, Job.FreelancerType.MULTIPLE)

    def test_detects_several(self):
        freelancer_type, _ = classify("We need several developers for this project.")
        self.assertEqual(freelancer_type, Job.FreelancerType.MULTIPLE)

    def test_detects_single_freelancer(self):
        freelancer_type, _ = classify("Looking for a freelancer to build a landing page.")
        self.assertEqual(freelancer_type, Job.FreelancerType.SINGLE)

    def test_detects_someone(self):
        freelancer_type, _ = classify("Need someone to fix a WordPress bug.")
        self.assertEqual(freelancer_type, Job.FreelancerType.SINGLE)

    def test_detects_singular_tester(self):
        freelancer_type, _ = classify("Need a tester to try out our beta app.")
        self.assertEqual(freelancer_type, Job.FreelancerType.SINGLE)

    def test_singular_role_pattern_catches_any_position(self):
        freelancer_type, _ = classify("Looking for a developer with React experience.")
        self.assertEqual(freelancer_type, Job.FreelancerType.SINGLE)

    def test_plural_testers_does_not_match_singular_tester_pattern(self):
        """Word-boundary check: 'testers' shouldn't accidentally satisfy
        the singular \\btester\\b pattern."""
        _, meta = classify("Need testers for our app.")
        self.assertNotIn(r"\btester\b", meta["single_hits"])

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
