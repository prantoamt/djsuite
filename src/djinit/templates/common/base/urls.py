from django.urls import path

from base.views import TaskStatusView

urlpatterns = [
    path("task-status/", TaskStatusView.as_view(), name="task-status"),
]
