"""
URL configuration for upwork_assistant project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from .views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", health_check, name="health_check"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("api/screenshots/", include("screenshots.urls")),
    path("gmail/", include("ingestion.urls")),
    path("jobs/", include("proposals.urls")),
    path("", include("jobs.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
