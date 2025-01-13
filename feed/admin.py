from django.contrib import admin

from .models import Like, Update


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "created_at", "like_count", "hidden")
    list_filter = ("hidden",)


admin.site.register(Like)
