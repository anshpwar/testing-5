"""Identify the calling profile from the X-Handle header (the fixture-grade stand-in for real sessions)."""
from django.conf import settings

from socialkit import handles

from .models import Profile


def current_profile(request):
    raw = request.META.get(getattr(settings, "HANDLE_HEADER", "HTTP_X_HANDLE"), "")
    handle = handles.normalize(raw)
    if not handle:
        return None
    return Profile.objects.filter(handle=handle).first()
