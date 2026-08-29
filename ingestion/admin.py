from django.contrib import admin

from .models import GmailCredential, GmailSyncState


@admin.register(GmailSyncState)
class GmailSyncStateAdmin(admin.ModelAdmin):
    list_display = ("last_history_id", "last_synced_at")

    def has_add_permission(self, request):
        return not GmailSyncState.objects.exists()


@admin.register(GmailCredential)
class GmailCredentialAdmin(admin.ModelAdmin):
    list_display = ("updated_at", "token_expiry")
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not GmailCredential.objects.exists()
