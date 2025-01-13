from django.urls import path

from . import views

urlpatterns = [
    path("", views.register, name="profile-register"),
    path("me/limits/", views.my_limits, name="profile-limits"),
    path("me/verify/", views.verify, name="profile-verify"),
    path("<str:handle>/", views.detail, name="profile-detail"),
]
