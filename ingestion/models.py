from django.db import models


class GmailSyncState(models.Model):
    """Singleton row tracking the Gmail History API cursor for incremental sync."""

    last_history_id = models.CharField(max_length=32, null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Gmail sync state"
        verbose_name_plural = "Gmail sync state"

    def __str__(self):
        return f"Gmail sync state (last synced {self.last_synced_at or 'never'})"

    @classmethod
    def load(cls) -> "GmailSyncState":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class GmailCredential(models.Model):
    """Singleton row holding the OAuth refresh token for the user's Gmail account."""

    refresh_token = models.CharField(max_length=512)
    token_expiry = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Gmail credential"
        verbose_name_plural = "Gmail credential"

    def __str__(self):
        return "Gmail OAuth credential"

    @classmethod
    def load(cls) -> "GmailCredential | None":
        return cls.objects.first()

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
