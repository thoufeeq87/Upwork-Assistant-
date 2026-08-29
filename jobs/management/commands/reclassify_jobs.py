from django.core.management.base import BaseCommand

from jobs.models import Job
from jobs.services.classification import classify


class Command(BaseCommand):
    help = "Re-run the freelancer-type heuristic against all jobs' snippet_text without re-ingesting."

    def handle(self, *args, **options):
        updated = 0
        for job in Job.objects.all():
            freelancer_type, meta = classify(job.snippet_text)
            if freelancer_type != job.freelancer_type or meta != job.classification_meta:
                job.freelancer_type = freelancer_type
                job.classification_meta = meta
                job.save(update_fields=["freelancer_type", "classification_meta", "updated_at"])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Reclassified {updated} job(s)."))
