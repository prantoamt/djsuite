import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_when_db_reachable_then_returns_200(api_client: APIClient) -> None:
    """Verify the health endpoint returns 200 with status 'healthy' when the database is reachable."""
    url = reverse("base:health-check")
    response = api_client.get(url)
    assert response.status_code == HTTP_200_OK
    assert response.data["status"] == "healthy"
