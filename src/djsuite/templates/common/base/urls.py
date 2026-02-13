from django.urls import path

from base.views import HealthCheckView, TaskStatusView

app_name = "base"

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("task-status/", TaskStatusView.as_view(), name="task-status"),
]
