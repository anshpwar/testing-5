"""Plain digest page built on the timeline context (added independently, scenario 100)."""
from django.shortcuts import get_object_or_404, render

from profiles.models import Profile
from socialkit.httpjson import parse_now

from . import views


def digest(request, handle):
    profile = get_object_or_404(Profile, handle=handle.lower())
    context = views.timeline_context(profile, parse_now(request.GET))
    return render(request, "feed/digest_100.html", context)
