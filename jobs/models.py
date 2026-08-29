from django.db import models


class Job(models.Model):
    class FreelancerType(models.TextChoices):
        SINGLE = "single", "Single freelancer"
        MULTIPLE = "multiple", "Multiple freelancers"
        UNKNOWN = "unknown", "Unknown"

    class Status(models.TextChoices):
        NEW = "new", "New"
        REVIEWED = "reviewed", "Reviewed"
        SCREENSHOTS_ADDED = "screenshots_added", "Screenshots added"
        HOOKS_GENERATED = "hooks_generated", "Hooks generated"
        PROPOSAL_READY = "proposal_ready", "Proposal ready"
        APPLIED = "applied", "Applied"
        SKIPPED = "skipped", "Skipped"

    job_uid = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        help_text="Upwork's job identifier (the ~token in the job URL). The real dedupe key.",
    )
    upwork_url = models.URLField(max_length=1000)
    title = models.CharField(max_length=500)
    snippet_text = models.TextField(
        blank=True,
        help_text="Short excerpt from the Gmail alert email — never the full job description.",
    )
    extracted_description = models.TextField(
        blank=True,
        help_text="Optionally populated from Claude's read of the screenshots at hook-generation time.",
    )
    freelancer_type = models.CharField(
        max_length=16, choices=FreelancerType.choices, default=FreelancerType.UNKNOWN
    )
    classification_meta = models.JSONField(
        default=dict, blank=True, help_text="Matched keywords/rules from the classifier, for debugging."
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.NEW)
    posted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
