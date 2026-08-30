from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import Job


class Command(BaseCommand):
    help = (
        "Deletes jobs (and their screenshots/hooks/proposals, via cascade) older "
        "than settings.JOB_RETENTION_DAYS. Favorited jobs are always exempt. "
        "Run this on a schedule (e.g. a Railway Cron Job) to keep the dashboard "
        "from growing forever."
    )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=settings.JOB_RETENTION_DAYS)
        old_jobs = Job.objects.filter(created_at__lt=cutoff, is_favorite=False)
        count = old_jobs.count()
        old_jobs.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Purged {count} job(s) older than {settings.JOB_RETENTION_DAYS} days "
                f"(favorited jobs kept regardless of age)."
            )
        )
