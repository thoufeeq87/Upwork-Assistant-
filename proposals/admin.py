from django.contrib import admin

from .models import Hook, HookFramework, Proposal, ProposalTemplate


@admin.register(HookFramework)
class HookFrameworkAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    list_filter = ("is_active",)


@admin.register(ProposalTemplate)
class ProposalTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "updated_at")
    list_filter = ("is_active", "category")


@admin.register(Hook)
class HookAdmin(admin.ModelAdmin):
    list_display = ("job", "selected", "created_at")
    list_filter = ("selected",)
    readonly_fields = ("claude_raw_response", "created_at")


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ("job", "hook", "created_at")
    readonly_fields = ("claude_raw_response", "created_at")
