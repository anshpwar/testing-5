"""Small helpers for JSON endpoints."""
import datetime as dt
import json
from functools import wraps

from django.http import JsonResponse
from django.utils import timezone

UTC = dt.timezone.utc


def read_json(request):
    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None
    return body if isinstance(body, dict) else None


def error(code, status=400, detail=""):
    payload = {"error": code}
    if detail:
        payload["detail"] = detail
    return JsonResponse(payload, status=status)


def parse_now(query):
    """The `now` query parameter as an aware UTC datetime; the real clock when it is absent."""
    raw = query.get("now")
    if not raw:
        return timezone.now()
    moment = dt.datetime.fromisoformat(raw)
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def require_profile(view):
    """Pass the calling profile (named by the X-Handle header) to the view, or answer 401."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        from profiles.auth import current_profile
        profile = current_profile(request)
        if profile is None:
            return error("unauthorized", status=401)
        return view(request, profile, *args, **kwargs)
    return wrapper
