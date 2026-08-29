from django.urls import path

from . import views

app_name = "ingestion"

urlpatterns = [
    path("connect/", views.connect, name="connect"),
    path("oauth2callback/", views.oauth_callback, name="oauth_callback"),
    path("sync/", views.sync_now, name="sync_now"),
]
