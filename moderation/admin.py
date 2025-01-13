from django.contrib import admin

from .models import Action, Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "update", "reporter", "reason", "status")
    list_filter = ("status", "reason")


admin.site.register(Action)
