from django.urls import path

from . import views

urlpatterns = [
    path("suggestions/", views.suggestions, name="follow-suggestions"),
    path("<str:handle>/", views.follow, name="follow-toggle"),
    path("<str:handle>/block/", views.block, name="follow-block"),
    path("<str:handle>/followers/", views.followers, name="follow-followers"),
]
