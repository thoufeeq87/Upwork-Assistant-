from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from jobs.models import Job

from . import services
from .models import Hook
from .services import ClaudeCallFailed


@login_required
@require_POST
def generate_hooks(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    try:
        hooks = services.generate_hooks(job)
        error = None
    except ClaudeCallFailed as exc:
        hooks = job.hooks.all()
        error = str(exc)
    return render(request, "proposals/_hooks.html", {"job": job, "hooks": hooks, "error": error})


@login_required
@require_POST
def select_hook(request, hook_id):
    hook = get_object_or_404(Hook, pk=hook_id)
    Hook.objects.filter(job=hook.job).update(selected=False)
    hook.selected = True
    hook.save(update_fields=["selected"])
    return render(request, "proposals/_hooks.html", {"job": hook.job, "hooks": hook.job.hooks.all(), "error": None})


@login_required
@require_POST
def generate_proposal(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    hook = job.hooks.filter(selected=True).first()
    if hook is None:
        return render(
            request,
            "proposals/_proposal.html",
            {"job": job, "proposal": None, "error": "Select a hook first."},
        )
    try:
        proposal = services.generate_proposal(job, hook)
        error = None
    except ClaudeCallFailed as exc:
        proposal = job.proposals.first()
        error = str(exc)
    return render(request, "proposals/_proposal.html", {"job": job, "proposal": proposal, "error": error})
