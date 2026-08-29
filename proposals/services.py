import anthropic

from . import claude_client
from .models import Hook, HookFramework, Proposal, ProposalTemplate


class ClaudeCallFailed(Exception):
    """Raised with a user-friendly message when a Claude API call can't complete."""


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except anthropic.RateLimitError:
        raise ClaudeCallFailed("Claude is rate-limited right now — try again in a moment.")
    except anthropic.APIConnectionError:
        raise ClaudeCallFailed("Couldn't reach the Claude API — check your connection and try again.")
    except anthropic.APIStatusError as exc:
        if exc.status_code >= 500:
            raise ClaudeCallFailed("Claude API is having issues right now — try again shortly.")
        raise ClaudeCallFailed(f"Claude API rejected the request: {exc.message}")


def generate_hooks(job, count: int = 10) -> list[Hook]:
    framework = HookFramework.objects.filter(is_active=True).first()
    if framework is None:
        raise ClaudeCallFailed("No active Hook Framework configured — add one in the admin panel first.")

    screenshots = list(job.screenshots.order_by("order", "uploaded_at"))
    if not screenshots:
        raise ClaudeCallFailed("This job has no screenshots yet — capture one with the Chrome extension first.")

    hook_texts, raw_response = _call(
        claude_client.generate_hooks, job, framework, screenshots, count=count
    )

    hooks = [
        Hook.objects.create(job=job, framework=framework, text=text, claude_raw_response=raw_response)
        for text in hook_texts
    ]

    job.status = job.Status.HOOKS_GENERATED
    job.save(update_fields=["status", "updated_at"])
    return hooks


def generate_proposal(job, hook: Hook) -> Proposal:
    template = ProposalTemplate.objects.filter(is_active=True).first()
    if template is None:
        raise ClaudeCallFailed("No active Proposal Template configured — add one in the admin panel first.")

    Hook.objects.filter(job=job).update(selected=False)
    hook.selected = True
    hook.save(update_fields=["selected"])

    text, raw_response = _call(claude_client.generate_proposal, job, hook.text, template)

    proposal = Proposal.objects.create(
        job=job, hook=hook, template=template, text=text, claude_raw_response=raw_response
    )

    job.status = job.Status.PROPOSAL_READY
    job.save(update_fields=["status", "updated_at"])
    return proposal
