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
    is_favorite = models.BooleanField(default=False, help_text="Starred jobs are also protected from the retention purge.")
    email_received_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When the Upwork alert email landed in Gmail (its internalDate) — not when Upwork itself posted the job.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class FreelancerTypeCorrection(models.Model):
    """A manual freelancer_type correction on a Job, with the reason the
    user gave. The reason is mined for keywords that feed LearnedKeyword,
    so future jobs with similar wording classify correctly automatically."""

    job = models.ForeignKey(Job, related_name="freelancer_type_corrections", on_delete=models.CASCADE)
    previous_type = models.CharField(max_length=16, choices=Job.FreelancerType.choices)
    corrected_type = models.CharField(max_length=16, choices=Job.FreelancerType.choices)
    reason = models.TextField(
        blank=True,
        help_text="Why this job is actually single/multiple — e.g. \"mentions team of 3 testers\". Mined for keywords the classifier learns from.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.job.title}: {self.previous_type} -> {self.corrected_type}"


class LearnedKeyword(models.Model):
    """A phrase mined from a correction's reason, associated with the
    freelancer_type it signals. classify_with_learned_keywords() checks
    these as a fallback when the static regex heuristic returns unknown."""

    phrase = models.CharField(max_length=100)
    freelancer_type = models.CharField(
        max_length=16,
        choices=[
            (Job.FreelancerType.SINGLE, "Single freelancer"),
            (Job.FreelancerType.MULTIPLE, "Multiple freelancers"),
        ],
    )
    weight = models.PositiveIntegerField(default=1, help_text="Incremented each time a new correction reinforces this phrase.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("phrase", "freelancer_type")
        ordering = ["-weight", "phrase"]

    def __str__(self):
        return f'"{self.phrase}" -> {self.freelancer_type} (x{self.weight})'
