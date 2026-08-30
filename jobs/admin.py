from django.contrib import admin

from .models import FreelancerTypeCorrection, Job, LearnedKeyword


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "freelancer_type", "status", "email_received_at", "created_at")
    list_filter = ("status", "freelancer_type")
    search_fields = ("title", "snippet_text", "job_uid", "upwork_url")
    readonly_fields = ("created_at", "updated_at")


@admin.register(FreelancerTypeCorrection)
class FreelancerTypeCorrectionAdmin(admin.ModelAdmin):
    list_display = ("job", "previous_type", "corrected_type", "created_at")
    list_filter = ("previous_type", "corrected_type")
    readonly_fields = ("created_at",)


@admin.register(LearnedKeyword)
class LearnedKeywordAdmin(admin.ModelAdmin):
    list_display = ("phrase", "freelancer_type", "weight", "updated_at")
    list_filter = ("freelancer_type",)
    search_fields = ("phrase",)
    ordering = ("-weight", "phrase")
