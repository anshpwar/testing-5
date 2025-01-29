from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from profiles.models import Profile
from socialkit.httpjson import parse_now

from . import services


def timeline_context(profile, now, cursor=None):
    """Template context for a profile's timeline page."""
    page = services.timeline(profile, now, cursor)
    return {"profile": profile, "items": page.items, "next_cursor": page.next_cursor}


@require_GET
def timeline_page(request, handle):
    profile = get_object_or_404(Profile, handle=handle.lower())
    context = timeline_context(profile, parse_now(request.GET), request.GET.get("cursor"))
    return render(request, "feed/timeline.html", context)
