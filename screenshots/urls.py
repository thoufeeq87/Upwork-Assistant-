from django.urls import path

from .api import ScreenshotUploadView

app_name = "screenshots"

urlpatterns = [
    path("", ScreenshotUploadView.as_view(), name="upload"),
]
