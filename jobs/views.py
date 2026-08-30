from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Job
from .services.classification import record_correction


@login_required
def dashboard(request):
    jobs = Job.objects.all()

    status = request.GET.get("status")
    if status:
        jobs = jobs.filter(status=status)

    freelancer_type = request.GET.get("freelancer_type")
    if freelancer_type:
        jobs = jobs.filter(freelancer_type=freelancer_type)

    return render(
        request,
        "jobs/dashboard.html",
        {
            "jobs": jobs,
            "status_choices": Job.Status.choices,
            "freelancer_type_choices": Job.FreelancerType.choices,
            "current_status": status or "",
            "current_freelancer_type": freelancer_type or "",
        },
    )


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
