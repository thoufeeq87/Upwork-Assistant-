from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "freelancer_type", "status", "posted_at", "created_at")
    list_filter = ("status", "freelancer_type")
    search_fields = ("title", "snippet_text", "job_uid", "upwork_url")
    readonly_fields = ("created_at", "updated_at")
