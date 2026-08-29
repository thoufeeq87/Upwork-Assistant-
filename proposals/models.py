from django.db import models

from jobs.models import Job


class HookFramework(models.Model):
    """A reusable 'headline + hook' framework used as the prompt for hook generation."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    prompt_template = models.TextField(help_text="Instructions given to Claude alongside the job screenshots.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "name"]

    def __str__(self):
        return self.name


class ProposalTemplate(models.Model):
    """A reusable proposal template used as the prompt for full-proposal generation."""

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, help_text="e.g. AI automation, Mobile QA")
    template_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "name"]

    def __str__(self):
        return self.name


class Hook(models.Model):
    job = models.ForeignKey(Job, related_name="hooks", on_delete=models.CASCADE)
    framework = models.ForeignKey(HookFramework, null=True, blank=True, on_delete=models.SET_NULL)
    text = models.TextField()
    selected = models.BooleanField(default=False)
    claude_raw_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text[:80]


class Proposal(models.Model):
    job = models.ForeignKey(Job, related_name="proposals", on_delete=models.CASCADE)
    hook = models.ForeignKey(Hook, related_name="proposals", on_delete=models.CASCADE)
    template = models.ForeignKey(ProposalTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    text = models.TextField()
    claude_raw_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Proposal for {self.job.title} ({self.created_at:%Y-%m-%d})"
