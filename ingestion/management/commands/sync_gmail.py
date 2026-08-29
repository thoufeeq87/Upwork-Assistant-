from django.core.management.base import BaseCommand

from ingestion.services import sync_new_alerts


class Command(BaseCommand):
    help = "Fetch new Upwork alert emails from Gmail and create Job rows. Run via Railway Cron Job."

    def handle(self, *args, **options):
        created = sync_new_alerts()
        self.stdout.write(self.style.SUCCESS(f"Synced Gmail — {created} new job(s) created."))
