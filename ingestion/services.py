from datetime import datetime

from django.conf import settings
from django.utils import timezone

from jobs.models import Job
from jobs.services.classification import classify

from . import gmail_client
from .models import GmailSyncState
from .parser import parse_alert_email


def sync_new_alerts() -> int:
    """Fetch new Upwork alert emails since the last sync, parse them, and
    create/update Job rows. Returns the number of new jobs created."""
    service = gmail_client.get_gmail_service()
    sync_state = GmailSyncState.load()

    message_ids = gmail_client.list_alert_message_ids(
        service, settings.GMAIL_ALERT_LABEL, sync_state.last_history_id
    )

    created = 0
    for message_id in message_ids:
        html, internal_date = gmail_client.get_message_html(service, message_id)
        for parsed in parse_alert_email(html):
            freelancer_type, meta = classify(parsed.snippet)
            _, was_created = Job.objects.get_or_create(
                job_uid=parsed.job_uid,
                defaults={
                    "title": parsed.title,
                    "snippet_text": parsed.snippet,
                    "upwork_url": parsed.url,
                    "freelancer_type": freelancer_type,
                    "classification_meta": meta,
                    "posted_at": datetime.fromisoformat(internal_date),
                },
            )
            if was_created:
                created += 1

    sync_state.last_history_id = gmail_client.get_current_history_id(service)
    sync_state.last_synced_at = timezone.now()
    sync_state.save()

    return created
