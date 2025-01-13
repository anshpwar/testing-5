from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("handle", "display_name", "joined_on", "verified", "strikes", "follower_count")
    search_fields = ("handle", "display_name")
    list_filter = ("verified", "moderator")
