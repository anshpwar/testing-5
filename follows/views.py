from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from profiles.models import Profile
from socialkit.httpjson import error, parse_now, require_profile

from . import services

STATUS = {"self_follow": 400, "self_block": 400, "blocked": 403, "daily_limit": 429, "following_cap": 429}


def _target(handle):
    try:
        return Profile.objects.get(handle=handle.lower())
    except Profile.DoesNotExist:
        raise Http404


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
@require_profile
def follow(request, profile, handle):
    target = _target(handle)
    if request.method == "DELETE":
        services.unfollow(profile, target)
        return JsonResponse({"following": False, "followers": Profile.objects.get(pk=target.pk).follower_count})
    try:
        created = services.follow(profile, target, parse_now(request.GET).date())
    except services.FollowError as exc:
        return error(exc.code, status=STATUS.get(exc.code, 400))
    return JsonResponse({"following": True, "followers": Profile.objects.get(pk=target.pk).follower_count}, status=201 if created else 200)


@csrf_exempt
@require_http_methods(["POST"])
@require_profile
def block(request, profile, handle):
    try:
        created = services.block(profile, _target(handle), parse_now(request.GET).date())
    except services.FollowError as exc:
        return error(exc.code, status=STATUS.get(exc.code, 400))
    return JsonResponse({"blocked": True}, status=201 if created else 200)


@require_GET
def followers(request, handle):
    target = _target(handle)
    handles = Profile.objects.filter(pk__in=services.follower_ids(target)).values_list("handle", flat=True)
    return JsonResponse({"handle": target.handle, "followers": sorted(handles)})


@require_GET
@require_profile
def suggestions(request, profile):
    order = services.suggestions(profile)
    picked = {p.pk: p.handle for p in Profile.objects.filter(pk__in=order)}
    return JsonResponse({"suggestions": [picked[pk] for pk in order]})
