from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from socialkit.httpjson import error, parse_now, read_json, require_profile

from . import services
from .models import Profile


@require_GET
def detail(request, handle):
    try:
        profile = Profile.objects.get(handle=handle.lower())
    except Profile.DoesNotExist:
        raise Http404
    return JsonResponse(services.summary(profile, parse_now(request.GET).date()))


@require_GET
@require_profile
def my_limits(request, profile):
    return JsonResponse(services.limits(profile, parse_now(request.GET).date()))


@csrf_exempt
@require_POST
def register(request):
    body = read_json(request)
    if not body or "handle" not in body or "display_name" not in body:
        return error("bad_request")
    joined = parse_now(request.GET).date()
    try:
        profile = services.register(body["handle"], body["display_name"], joined, body.get("bio", ""))
    except ValueError as exc:
        status = 409 if str(exc) == "handle taken" else 400
        return error("invalid", status=status, detail=str(exc))
    return JsonResponse(services.summary(profile, joined), status=201)


@csrf_exempt
@require_POST
@require_profile
def verify(request, profile):
    status = services.apply_verification(profile, parse_now(request.GET).date())
    return JsonResponse(dict(status, verified=profile.verified))
