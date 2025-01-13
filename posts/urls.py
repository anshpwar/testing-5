from django.urls import path

from . import api

urlpatterns = [path("<str:ref>/", api.summary, name="entry-summary")]
