from jobs.models import Job

from .models import JobScreenshot


def attach_screenshot(job: Job, image) -> JobScreenshot:
    """Attaches an image file to `job` as the next screenshot in reading
    order, and bumps the job to screenshots_added if it's still new/
    reviewed. Shared by the Chrome extension's API endpoint and the
    in-app manual upload (for devices, like an iPad, that can't run a
    Chrome extension at all)."""
    next_order = job.screenshots.count()
    screenshot = JobScreenshot.objects.create(job=job, image=image, order=next_order)

    if job.status in (Job.Status.NEW, Job.Status.REVIEWED):
        job.status = Job.Status.SCREENSHOTS_ADDED
        job.save(update_fields=["status", "updated_at"])

    return screenshot
