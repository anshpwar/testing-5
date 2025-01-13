from django.http import Http404, JsonResponse

from .models import Post


def summary(request, ref):
    try:
        obj = Post.objects.get(ref=ref)
    except Post.DoesNotExist:
        raise Http404
    return JsonResponse({"ref": obj.ref, "amount_cents": obj.amount_cents, "status": obj.status})
