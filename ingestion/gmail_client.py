"""
Gmail API OAuth2 + fetch wrapper. Read-only scope only — this app never
sends, modifies, or deletes anything in the user's mailbox.
"""

import base64
from datetime import datetime, timezone

from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from .models import GmailCredential

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def build_flow(redirect_uri: str, *, state: str | None = None, code_verifier: str | None = None) -> Flow:
    """Builds a Flow for the authorize step, or (with `state`/`code_verifier`
    from the session) an equivalent Flow for the callback step — PKCE means
    the code_verifier generated when building the authorization URL must be
    reused for the token exchange, and since each step is a separate HTTP
    request/Flow instance, the caller is responsible for round-tripping both
    through the session in between."""
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        state=state,
        code_verifier=code_verifier,
    )


def save_credentials_from_flow(flow: Flow) -> None:
    creds = flow.credentials
    GmailCredential.objects.update_or_create(
        pk=1,
        defaults={
            "refresh_token": creds.refresh_token,
            "token_expiry": creds.expiry,
        },
    )


def _load_credentials() -> Credentials | None:
    stored = GmailCredential.load()
    if stored is None:
        return None

    creds = Credentials(
        token=None,
        refresh_token=stored.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def get_gmail_service():
    creds = _load_credentials()
    if creds is None:
        raise RuntimeError("Gmail is not connected yet — visit /gmail/connect/ to authorize.")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_alert_message_ids(service, label_name: str, after_history_id: str | None) -> list[str]:
    """Return Gmail message IDs for the alert label, newest activity first.

    Uses the History API for incremental sync when a cursor is available,
    falling back to a plain label search on first run.
    """
    label_id = _resolve_label_id(service, label_name)

    if after_history_id:
        message_ids = []
        page_token = None
        while True:
            resp = (
                service.users()
                .history()
                .list(
                    userId="me",
                    startHistoryId=after_history_id,
                    labelId=label_id,
                    historyTypes=["messageAdded"],
                    pageToken=page_token,
                )
                .execute()
            )
            for record in resp.get("history", []):
                for added in record.get("messagesAdded", []):
                    message_ids.append(added["message"]["id"])
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return message_ids

    message_ids = []
    page_token = None
    while True:
        resp = (
            service.users()
            .messages()
            .list(userId="me", labelIds=[label_id], pageToken=page_token, maxResults=100)
            .execute()
        )
        message_ids.extend(m["id"] for m in resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return message_ids


def _resolve_label_id(service, label_name: str) -> str:
    resp = service.users().labels().list(userId="me").execute()
    for label in resp.get("labels", []):
        if label["name"] == label_name:
            return label["id"]
    raise RuntimeError(
        f"Gmail label '{label_name}' not found — create it and label your Upwork alert "
        f"emails with it (see GMAIL_ALERT_LABEL setting)."
    )


def get_message_html(service, message_id: str) -> tuple[str, str]:
    """Returns (html_body, internal_date_iso) for a Gmail message."""
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()

    html = _extract_html_part(msg["payload"])
    internal_date = datetime.fromtimestamp(int(msg["internalDate"]) / 1000, tz=timezone.utc)
    return html, internal_date.isoformat()


def _extract_html_part(payload: dict) -> str:
    if payload.get("mimeType") == "text/html" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        html = _extract_html_part(part)
        if html:
            return html
    return ""


def get_current_history_id(service) -> str:
    profile = service.users().getProfile(userId="me").execute()
    return str(profile["historyId"])
