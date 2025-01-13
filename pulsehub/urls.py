from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("profiles/", include("profiles.urls")),
    path("follows/", include("follows.urls")),
    path("feed/", include("feed.urls")),
    path("moderation/", include("moderation.urls")),
    path("entries/", include("posts.urls")),
]
