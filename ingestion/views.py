from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import gmail_client, services


@login_required
def connect(request):
    redirect_uri = request.build_absolute_uri(reverse("ingestion:oauth_callback"))
    flow = gmail_client.build_flow(redirect_uri)
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    # PKCE: the code_verifier used to build this URL must be reused for the
    # token exchange in oauth_callback, which runs as a separate request
    # against a fresh Flow instance — round-trip both through the session.
    request.session["gmail_oauth_state"] = state
    request.session["gmail_oauth_code_verifier"] = flow.code_verifier
    return redirect(auth_url)


@login_required
def oauth_callback(request):
    redirect_uri = request.build_absolute_uri(reverse("ingestion:oauth_callback"))
    state = request.session.pop("gmail_oauth_state", None)
    code_verifier = request.session.pop("gmail_oauth_code_verifier", None)
    flow = gmail_client.build_flow(redirect_uri, state=state, code_verifier=code_verifier)
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    gmail_client.save_credentials_from_flow(flow)
    messages.success(request, "Gmail connected.")
    return redirect("jobs:dashboard")


@login_required
@require_POST
def sync_now(request):
    try:
        created = services.sync_new_alerts()
        messages.success(request, f"Sync complete — {created} new job(s).")
    except RuntimeError as exc:
        messages.error(request, str(exc))
    return redirect("jobs:dashboard")
