from django.core.management.base import BaseCommand

from jobs.models import Job
from jobs.services.classification import classify_with_learned_keywords


class Command(BaseCommand):
    help = (
        "Re-run the freelancer-type heuristic (including learned keywords from "
        "corrections) against jobs' snippet_text without re-ingesting. Skips any "
        "job with a manual correction on record, so this never overwrites a "
        "correction you already made."
    )

    def handle(self, *args, **options):
        updated = 0
        jobs = Job.objects.filter(freelancer_type_corrections__isnull=True)
        for job in jobs:
            freelancer_type, meta = classify_with_learned_keywords(job.snippet_text)
            if freelancer_type != job.freelancer_type or meta != job.classification_meta:
                job.freelancer_type = freelancer_type
                job.classification_meta = meta
                job.save(update_fields=["freelancer_type", "classification_meta", "updated_at"])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Reclassified {updated} job(s)."))
