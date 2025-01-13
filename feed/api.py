from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from socialkit.httpjson import error, parse_now, read_json, require_profile

from . import services
from .models import Update

POST_STATUS = {"empty": 422, "too_long": 422, "blocked_term": 422, "hidden": 409, "daily_limit": 429,
               "muted": 403, "suspended": 403}


def serialize_update(update, liked=False):
    """JSON shape of one update, shared by the timeline, publish and like endpoints."""
    return {
        "id": update.pk,
        "author": {
            "handle": update.author.handle,
            "display_name": update.author.display_name,
            "verified": update.author.verified,
        },
        "body": update.body,
        "created_at": update.created_at.isoformat(),
        "like_count": update.like_count,
        "reply_count": update.reply_count,
        "liked": liked,
    }


@require_GET
@require_profile
def timeline(request, profile):
    try:
        page = services.timeline(profile, parse_now(request.GET), request.GET.get("cursor"))
    except ValueError:
        return error("bad_cursor")
    liked = services.liked_ids(profile, page.items)
    return JsonResponse({"items": [serialize_update(u, u.pk in liked) for u in page.items], "next_cursor": page.next_cursor})


@csrf_exempt
@require_POST
@require_profile
def publish(request, profile):
    body = read_json(request)
    if body is None or "body" not in body:
        return error("bad_request")
    parent = None
    if body.get("parent") is not None:
        try:
            parent = Update.objects.get(pk=body["parent"])
        except (Update.DoesNotExist, ValueError, TypeError):
            return error("unknown_parent", status=404)
    try:
        update = services.publish(profile, body["body"], parse_now(request.GET), parent=parent)
    except services.PostError as exc:
        return error(exc.code, status=POST_STATUS.get(exc.code, 400))
    return JsonResponse(serialize_update(update), status=201)


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
@require_profile
def like(request, profile, pk):
    try:
        update = Update.objects.select_related("author").get(pk=pk)
    except Update.DoesNotExist:
        raise Http404
    try:
        if request.method == "POST":
            services.like(profile, update)
        else:
            services.unlike(profile, update)
    except services.PostError as exc:
        return error(exc.code, status=POST_STATUS.get(exc.code, 400))
    return JsonResponse(serialize_update(update, liked=request.method == "POST"))


@require_GET
def trending(request):
    now = parse_now(request.GET)
    return JsonResponse({"tags": [{"tag": tag, "count": n} for tag, n in services.trending(now)]})
