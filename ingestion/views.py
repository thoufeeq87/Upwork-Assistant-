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
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    return redirect(auth_url)


@login_required
def oauth_callback(request):
    redirect_uri = request.build_absolute_uri(reverse("ingestion:oauth_callback"))
    flow = gmail_client.build_flow(redirect_uri)
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
