from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Job
from .services.classification import record_correction
from .utils import extract_job_uid

JOBS_PER_PAGE = 10


@login_required
def dashboard(request):
    jobs = Job.objects.all()

    status = request.GET.get("status")
    if status:
        jobs = jobs.filter(status=status)
    else:
        # Thumbs-down soft-hides a job by marking it Skipped — the default
        # "All" view should exclude those. The Skipped tab still shows them.
        jobs = jobs.exclude(status=Job.Status.SKIPPED)

    freelancer_type = request.GET.get("freelancer_type")
    if freelancer_type:
        jobs = jobs.filter(freelancer_type=freelancer_type)

    favorites_only = request.GET.get("favorite") == "1"
    if favorites_only:
        jobs = jobs.filter(is_favorite=True)

    paginator = Paginator(jobs, JOBS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Pagination links need the current filters carried over, minus any
    # existing page number (each link sets its own).
    querydict = request.GET.copy()
    querydict.pop("page", None)
    base_querystring = querydict.urlencode()

    return render(
        request,
        "jobs/dashboard.html",
        {
            "jobs": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "base_querystring": base_querystring,
            "status_choices": Job.Status.choices,
            "freelancer_type_choices": Job.FreelancerType.choices,
            "current_status": status or "",
            "current_freelancer_type": freelancer_type or "",
            "favorites_only": favorites_only,
        },
    )


@login_required
def add_job(request):
    """Manually adds a job you found directly on Upwork (rather than via a
    Gmail alert) so it goes through the exact same screenshot -> hooks ->
    proposal flow as synced jobs. Only needs the job's Upwork URL, from
    which job_uid is extracted — the same identifier the Chrome extension
    matches screenshots against."""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        upwork_url = request.POST.get("upwork_url", "").strip()
        snippet_text = request.POST.get("snippet_text", "").strip()
        freelancer_type = request.POST.get("freelancer_type") or Job.FreelancerType.UNKNOWN

        errors = []
        if not title:
            errors.append("Title is required.")
        if not upwork_url:
            errors.append("Upwork URL is required.")

        job_uid = extract_job_uid(upwork_url) if upwork_url else None
        if upwork_url and not job_uid:
            errors.append("Couldn't find a job ID in that URL — paste the job's URL from your browser's address bar.")

        if not errors and job_uid:
            existing = Job.objects.filter(job_uid=job_uid).first()
            if existing:
                messages.info(request, "This job is already in your list.")
                return redirect("jobs:detail", pk=existing.pk)

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(
                request,
                "jobs/add_job.html",
                {
                    "freelancer_type_choices": Job.FreelancerType.choices,
                    "form_values": request.POST,
                },
            )

        job = Job.objects.create(
            title=title,
            upwork_url=upwork_url,
            job_uid=job_uid,
            snippet_text=snippet_text,
            freelancer_type=freelancer_type,
        )
        messages.success(request, "Job added — capture a screenshot with the Chrome extension whenever you're ready.")
        return redirect("jobs:detail", pk=job.pk)

    return render(request, "jobs/add_job.html", {"freelancer_type_choices": Job.FreelancerType.choices, "form_values": {}})


@login_required
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(
        request,
        "jobs/detail.html",
        {"job": job, "freelancer_type_choices": Job.FreelancerType.choices},
    )


@login_required
@require_POST
def correct_freelancer_type(request, pk):
    job = get_object_or_404(Job, pk=pk)
    corrected_type = request.POST.get("freelancer_type", "")
    reason = request.POST.get("reason", "").strip()

    if corrected_type in Job.FreelancerType.values:
        record_correction(job, corrected_type, reason)

    return redirect("jobs:detail", pk=job.pk)


@login_required
@require_POST
def toggle_favorite(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.is_favorite = not job.is_favorite
    job.save(update_fields=["is_favorite", "updated_at"])

    if request.headers.get("HX-Request"):
        return render(request, "jobs/_favorite_button.html", {"job": job})
    return redirect(request.META.get("HTTP_REFERER") or "jobs:dashboard")


@login_required
@require_POST
def skip_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.status = Job.Status.SKIPPED
    job.save(update_fields=["status", "updated_at"])

    if request.headers.get("HX-Request"):
        # Card disappears from the current list; the job itself is kept
        # (soft-hide, not deleted) and still reachable via the Skipped filter.
        return HttpResponse("")
    return redirect(request.META.get("HTTP_REFERER") or "jobs:dashboard")


@login_required
@require_POST
def mark_applied(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.status = Job.Status.APPLIED
    job.save(update_fields=["status", "updated_at"])

    # Unlike favorite/skip, this isn't a quiet htmx update — applying is a
    # milestone worth seeing land, so send the user to the dashboard's
    # Applied filter as a visible confirmation.
    return redirect(f"{reverse('jobs:dashboard')}?status={Job.Status.APPLIED}")
