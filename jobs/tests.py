from datetime import timedelta

from django.test import Client, SimpleTestCase, TestCase
from django.contrib.auth.models import User

from .models import FreelancerTypeCorrection, Job, LearnedKeyword
from .services.classification import classify, classify_with_learned_keywords, record_correction
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


class LearningFromCorrectionsTests(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            title="Mystery job",
            upwork_url="https://www.upwork.com/jobs/~999",
            job_uid="~999",
            snippet_text="This posting mentions a crew of testers needed for the sprint.",
            freelancer_type=Job.FreelancerType.UNKNOWN,
        )

    def test_record_correction_updates_job_and_creates_history(self):
        record_correction(self.job, Job.FreelancerType.MULTIPLE, reason="mentions crew of testers")
        self.job.refresh_from_db()
        self.assertEqual(self.job.freelancer_type, Job.FreelancerType.MULTIPLE)
        self.assertEqual(FreelancerTypeCorrection.objects.filter(job=self.job).count(), 1)
        correction = FreelancerTypeCorrection.objects.get(job=self.job)
        self.assertEqual(correction.previous_type, Job.FreelancerType.UNKNOWN)
        self.assertEqual(correction.corrected_type, Job.FreelancerType.MULTIPLE)

    def test_record_correction_learns_keywords_from_reason(self):
        record_correction(self.job, Job.FreelancerType.MULTIPLE, reason="mentions crew of testers")
        self.assertTrue(LearnedKeyword.objects.filter(phrase="crew", freelancer_type=Job.FreelancerType.MULTIPLE).exists())
        self.assertTrue(
            LearnedKeyword.objects.filter(phrase="crew testers", freelancer_type=Job.FreelancerType.MULTIPLE).exists()
        )
        # Filler words from the reason shouldn't become keywords.
        self.assertFalse(LearnedKeyword.objects.filter(phrase="mentions").exists())

    def test_repeated_reason_increments_weight_instead_of_duplicating(self):
        record_correction(self.job, Job.FreelancerType.MULTIPLE, reason="says crew needed")
        other_job = Job.objects.create(
            title="Another job", upwork_url="https://www.upwork.com/jobs/~998", job_uid="~998"
        )
        record_correction(other_job, Job.FreelancerType.MULTIPLE, reason="says crew again")
        keyword = LearnedKeyword.objects.get(phrase="crew", freelancer_type=Job.FreelancerType.MULTIPLE)
        self.assertEqual(keyword.weight, 2)

    def test_classify_with_learned_keywords_falls_back_when_static_is_unknown(self):
        record_correction(self.job, Job.FreelancerType.MULTIPLE, reason="mentions a crew for this")
        # A brand new job whose snippet contains the learned phrase, but
        # nothing the static regex heuristic would catch on its own.
        freelancer_type, meta = classify_with_learned_keywords("Small crew wanted for a weekend shoot.")
        self.assertEqual(freelancer_type, Job.FreelancerType.MULTIPLE)
        self.assertIn("crew", meta["learned_multiple_hits"])

    def test_static_heuristic_still_wins_over_learned_keywords(self):
        """A learned keyword must never override a confident static match."""
        record_correction(self.job, Job.FreelancerType.MULTIPLE, reason="mentions crew")
        freelancer_type, meta = classify_with_learned_keywords("Looking for a freelancer — small crew project.")
        self.assertEqual(freelancer_type, Job.FreelancerType.SINGLE)
        self.assertNotIn("learned_multiple_hits", meta)

    def test_reclassify_jobs_skips_manually_corrected_jobs(self):
        from django.core.management import call_command

        record_correction(self.job, Job.FreelancerType.SINGLE, reason="actually just one tester")
        self.job.refresh_from_db()
        self.assertEqual(self.job.freelancer_type, Job.FreelancerType.SINGLE)

        call_command("reclassify_jobs")

        self.job.refresh_from_db()
        # Static/learned heuristics would call this snippet MULTIPLE (it
        # matches "testers"), but the manual correction must survive.
        self.assertEqual(self.job.freelancer_type, Job.FreelancerType.SINGLE)


class CorrectFreelancerTypeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="testpass123")
        self.job = Job.objects.create(
            title="Test job", upwork_url="https://www.upwork.com/jobs/~1", job_uid="~1"
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_post_updates_freelancer_type_and_redirects(self):
        resp = self.client.post(
            f"/jobs/{self.job.pk}/correct-freelancer-type/",
            {"freelancer_type": Job.FreelancerType.MULTIPLE, "reason": "mentions a small crew"},
        )
        self.assertEqual(resp.status_code, 302)
        self.job.refresh_from_db()
        self.assertEqual(self.job.freelancer_type, Job.FreelancerType.MULTIPLE)
        self.assertEqual(FreelancerTypeCorrection.objects.filter(job=self.job).count(), 1)

    def test_requires_login(self):
        anon_client = Client()
        resp = anon_client.post(
            f"/jobs/{self.job.pk}/correct-freelancer-type/",
            {"freelancer_type": Job.FreelancerType.MULTIPLE, "reason": ""},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.get("Location", ""))


class FavoriteAndSkipTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin2", password="testpass123")
        self.job = Job.objects.create(
            title="Toggle job", upwork_url="https://www.upwork.com/jobs/~2", job_uid="~2"
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_toggle_favorite_flips_flag(self):
        self.assertFalse(self.job.is_favorite)
        self.client.post(f"/jobs/{self.job.pk}/toggle-favorite/")
        self.job.refresh_from_db()
        self.assertTrue(self.job.is_favorite)
        self.client.post(f"/jobs/{self.job.pk}/toggle-favorite/")
        self.job.refresh_from_db()
        self.assertFalse(self.job.is_favorite)

    def test_toggle_favorite_htmx_returns_button_partial_not_whole_card(self):
        resp = self.client.post(f"/jobs/{self.job.pk}/toggle-favorite/", HTTP_HX_REQUEST="true")
        content = resp.content.decode()
        self.assertIn("favorite-btn", content)
        # Must not be the full card partial (no snippet text or "Open on Upwork").
        self.assertNotIn("Open on Upwork", content)

    def test_skip_sets_status_and_does_not_delete(self):
        self.client.post(f"/jobs/{self.job.pk}/skip/")
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.Status.SKIPPED)
        self.assertTrue(Job.objects.filter(pk=self.job.pk).exists())

    def test_skip_htmx_returns_empty_response(self):
        resp = self.client.post(f"/jobs/{self.job.pk}/skip/", HTTP_HX_REQUEST="true")
        self.assertEqual(resp.content, b"")

    def test_dashboard_excludes_skipped_by_default(self):
        self.client.post(f"/jobs/{self.job.pk}/skip/")
        resp = self.client.get("/")
        self.assertNotIn(self.job.title, resp.content.decode())

    def test_dashboard_shows_skipped_under_explicit_filter(self):
        self.client.post(f"/jobs/{self.job.pk}/skip/")
        resp = self.client.get(f"/?status={Job.Status.SKIPPED}")
        self.assertIn(self.job.title, resp.content.decode())

    def test_dashboard_favorites_only_filter(self):
        other = Job.objects.create(
            title="Not favorited", upwork_url="https://www.upwork.com/jobs/~3", job_uid="~3"
        )
        self.client.post(f"/jobs/{self.job.pk}/toggle-favorite/")
        resp = self.client.get("/?favorite=1")
        content = resp.content.decode()
        self.assertIn(self.job.title, content)
        self.assertNotIn(other.title, content)


class MarkAppliedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin3", password="testpass123")
        self.job = Job.objects.create(
            title="Apply job", upwork_url="https://www.upwork.com/jobs/~4", job_uid="~4"
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_marks_status_applied(self):
        self.assertNotEqual(self.job.status, Job.Status.APPLIED)
        self.client.post(f"/jobs/{self.job.pk}/mark-applied/")
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.Status.APPLIED)

    def test_redirects_to_applied_filter(self):
        resp = self.client.post(f"/jobs/{self.job.pk}/mark-applied/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"status={Job.Status.APPLIED}", resp.get("Location", ""))

    def test_job_still_shown_under_applied_filter(self):
        self.client.post(f"/jobs/{self.job.pk}/mark-applied/")
        resp = self.client.get(f"/?status={Job.Status.APPLIED}")
        self.assertIn(self.job.title, resp.content.decode())

    def test_mark_applied_button_hidden_once_already_applied(self):
        self.client.post(f"/jobs/{self.job.pk}/mark-applied/")
        resp = self.client.get(f"/jobs/{self.job.pk}/")
        self.assertNotIn("Mark as applied", resp.content.decode())

    def test_requires_login(self):
        anon_client = Client()
        resp = anon_client.post(f"/jobs/{self.job.pk}/mark-applied/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.get("Location", ""))


class PurgeOldJobsTests(TestCase):
    def test_purges_only_jobs_older_than_retention_and_not_favorited(self):
        from django.core.management import call_command
        from django.utils import timezone

        old_job = Job.objects.create(
            title="Old job", upwork_url="https://www.upwork.com/jobs/~10", job_uid="~10"
        )
        Job.objects.filter(pk=old_job.pk).update(created_at=timezone.now() - timedelta(days=15))

        old_favorite = Job.objects.create(
            title="Old favorite", upwork_url="https://www.upwork.com/jobs/~11", job_uid="~11", is_favorite=True
        )
        Job.objects.filter(pk=old_favorite.pk).update(created_at=timezone.now() - timedelta(days=15))

        recent_job = Job.objects.create(
            title="Recent job", upwork_url="https://www.upwork.com/jobs/~12", job_uid="~12"
        )

        call_command("purge_old_jobs")

        self.assertFalse(Job.objects.filter(pk=old_job.pk).exists())
        self.assertTrue(Job.objects.filter(pk=old_favorite.pk).exists())
        self.assertTrue(Job.objects.filter(pk=recent_job.pk).exists())

    def test_purge_cascades_to_screenshots(self):
        from django.core.management import call_command
        from django.core.files.base import ContentFile
        from django.utils import timezone
        from screenshots.models import JobScreenshot

        old_job = Job.objects.create(
            title="Old job with screenshot", upwork_url="https://www.upwork.com/jobs/~13", job_uid="~13"
        )
        Job.objects.filter(pk=old_job.pk).update(created_at=timezone.now() - timedelta(days=15))
        shot = JobScreenshot(job=old_job, order=0)
        shot.image.save("test.png", ContentFile(b"fake-png-bytes"), save=True)
        shot_id = shot.id

        call_command("purge_old_jobs")

        self.assertFalse(JobScreenshot.objects.filter(pk=shot_id).exists())


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
