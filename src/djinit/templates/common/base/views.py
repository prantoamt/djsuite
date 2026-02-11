"""Base views module."""

from celery.result import AsyncResult
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView


class TaskStatusView(APIView):
    """
    View to check the status of a Celery task.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Check Task Status",
        description="Retrieve the status of a Celery task by its ID. "
        "This endpoint provides information on whether the task "
        "is pending, completed, failed, or in another state.",
        parameters=[
            OpenApiParameter(
                name="task_id",
                description="The ID of the Celery task to check.",
                required=True,
                type=str,
                examples=[
                    OpenApiExample(
                        "Example Task ID",
                        value="123e4567-e89b-12d3-a456-426614174000",
                        description="A sample UUID for a Celery task.",
                    )
                ],
            )
        ],
        responses={
            HTTP_200_OK: OpenApiResponse(
                description="Task completed successfully.",
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "Completed"},
                        "result": {
                            "type": "string",
                            "example": "Your result data here",
                        },
                    },
                },
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve the status of a Celery task by its ID.
        """
        task_id = request.GET.get("task_id")
        if not task_id:
            raise ValidationError({"task_id": "This query parameter is required."})

        result = AsyncResult(task_id)

        if result.state == "PENDING":
            return Response({"status": result.state}, status=HTTP_200_OK)

        if result.state == "SUCCESS":
            return Response(
                {"status": result.state, "result": result.result},
                status=HTTP_200_OK,
            )

        if result.state == "FAILURE":
            raise APIException(detail=result.result)

        return Response({"status": result.state}, status=HTTP_200_OK)
