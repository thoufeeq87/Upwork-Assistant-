from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from jobs.models import Job

from .models import JobScreenshot
from .services import attach_screenshot

# 1x1 transparent PNG
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08"
    b"\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00"
    b"\x05\xfe\x02\xfeA\xf3\x1f\xd8\x00\x00\x00\x00IEND\xaeB`\x82"
)


def make_png(name="shot.png"):
    return SimpleUploadedFile(name, PNG_BYTES, content_type="image/png")


class AttachScreenshotServiceTests(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            title="Service test job", upwork_url="https://www.upwork.com/jobs/~1", job_uid="~1"
        )

    def test_first_screenshot_gets_order_zero_and_updates_status(self):
        shot = attach_screenshot(self.job, make_png())
        self.assertEqual(shot.order, 0)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.Status.SCREENSHOTS_ADDED)

    def test_subsequent_screenshots_increment_order(self):
        attach_screenshot(self.job, make_png("a.png"))
        second = attach_screenshot(self.job, make_png("b.png"))
        third = attach_screenshot(self.job, make_png("c.png"))
        self.assertEqual(second.order, 1)
        self.assertEqual(third.order, 2)

    def test_does_not_downgrade_a_later_status(self):
        self.job.status = Job.Status.PROPOSAL_READY
        self.job.save(update_fields=["status"])
        attach_screenshot(self.job, make_png())
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.Status.PROPOSAL_READY)


class ScreenshotUploadAPITests(TestCase):
    """Extension endpoint — verifies the refactor onto attach_screenshot()
    didn't change its behavior."""

    def setUp(self):
        settings.EXTENSION_API_TOKEN = "test-token"
        self.job = Job.objects.create(
            title="API test job",
            upwork_url="https://www.upwork.com/jobs/~2",
            job_uid="~2",
        )
        self.client = Client()

    def test_valid_upload_creates_screenshot(self):
        resp = self.client.post(
            "/api/screenshots/",
            {"tab_url": self.job.upwork_url, "image": make_png()},
            HTTP_AUTHORIZATION="Token test-token",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(JobScreenshot.objects.filter(job=self.job).count(), 1)

    def test_wrong_token_rejected(self):
        resp = self.client.post(
            "/api/screenshots/",
            {"tab_url": self.job.upwork_url, "image": make_png()},
            HTTP_AUTHORIZATION="Token wrong",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(JobScreenshot.objects.count(), 0)

    def test_unknown_job_uid_returns_404(self):
        resp = self.client.post(
            "/api/screenshots/",
            {"tab_url": "https://www.upwork.com/jobs/~999999999", "image": make_png()},
            HTTP_AUTHORIZATION="Token test-token",
        )
        self.assertEqual(resp.status_code, 404)
