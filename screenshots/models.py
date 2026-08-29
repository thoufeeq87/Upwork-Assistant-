from django.db import models

from jobs.models import Job


class JobScreenshot(models.Model):
    job = models.ForeignKey(Job, related_name="screenshots", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="job_screenshots/%Y/%m/")
    order = models.PositiveSmallIntegerField(default=0, help_text="Reading order for multi-screenshot jobs.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["job", "order", "uploaded_at"]

    def __str__(self):
        return f"Screenshot #{self.order} for {self.job.title}"
