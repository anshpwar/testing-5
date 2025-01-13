from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from feed.models import Update
from socialkit.httpjson import error, parse_now, read_json, require_profile

from . import services


def _update(pk):
    try:
        return Update.objects.select_related("author").get(pk=pk)
    except Update.DoesNotExist:
        raise Http404


@csrf_exempt
@require_POST
@require_profile
def report(request, profile):
    body = read_json(request)
    if not body or "update_id" not in body:
        return error("bad_request")
    try:
        filed = services.file_report(profile, _update(body["update_id"]), body.get("reason", "other"), parse_now(request.GET))
    except services.ReportError as exc:
        return error(exc.code, status=429 if exc.code == "cooldown" else 409)
    return JsonResponse({"id": filed.pk, "status": filed.status, "hidden": filed.update.hidden}, status=201)


@require_GET
@require_profile
def queue(request, profile):
    if not profile.moderator:
        return error("forbidden", status=403)
    rows = [{"update_id": r["update"].pk, "author": r["update"].author.handle, "reports": len(r["reports"]), "hidden": r["hidden"]}
            for r in services.queue()]
    return JsonResponse({"queue": rows})


@csrf_exempt
@require_POST
@require_profile
def resolve(request, profile, pk):
    if not profile.moderator:
        return error("forbidden", status=403)
    body = read_json(request)
    if not body or "decision" not in body:
        return error("bad_request")
    try:
        author = services.resolve(_update(pk), body["decision"], parse_now(request.GET))
    except services.ReportError as exc:
        return error(exc.code, status=409)
    return JsonResponse({"strikes": author.strikes, "handle": author.handle})
