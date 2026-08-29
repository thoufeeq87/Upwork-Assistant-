from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Job


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
    return render(request, "jobs/detail.html", {"job": job})
