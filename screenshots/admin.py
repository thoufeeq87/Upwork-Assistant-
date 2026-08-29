from django.contrib import admin

from .models import JobScreenshot


@admin.register(JobScreenshot)
class JobScreenshotAdmin(admin.ModelAdmin):
    list_display = ("job", "order", "uploaded_at")
    list_filter = ("job",)
    ordering = ("job", "order")
