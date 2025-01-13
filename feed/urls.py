from django.urls import path

from . import api, views

urlpatterns = [
    path("timeline/", api.timeline, name="feed-timeline"),
    path("publish/", api.publish, name="feed-publish"),
    path("trending/", api.trending, name="feed-trending"),
    path("<int:pk>/like/", api.like, name="feed-like"),
    path("page/<str:handle>/", views.timeline_page, name="feed-page"),
]
