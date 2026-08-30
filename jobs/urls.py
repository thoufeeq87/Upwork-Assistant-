from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("jobs/<int:pk>/", views.job_detail, name="detail"),
    path("jobs/<int:pk>/correct-freelancer-type/", views.correct_freelancer_type, name="correct_freelancer_type"),
]
