from django.urls import path

from . import views

urlpatterns = [
    path("reports/", views.report, name="moderation-report"),
    path("queue/", views.queue, name="moderation-queue"),
    path("updates/<int:pk>/resolve/", views.resolve, name="moderation-resolve"),
]
