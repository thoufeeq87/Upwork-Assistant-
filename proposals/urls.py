from django.urls import path

from . import views

app_name = "proposals"

urlpatterns = [
    path("<int:job_id>/generate-hooks/", views.generate_hooks, name="generate_hooks"),
    path("hooks/<int:hook_id>/select/", views.select_hook, name="select_hook"),
    path("<int:job_id>/generate-proposal/", views.generate_proposal, name="generate_proposal"),
]
