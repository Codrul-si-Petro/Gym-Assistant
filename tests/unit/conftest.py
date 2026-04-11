import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    """
    Logged in test user.
    """
    client = APIClient()
    user = User.objects.create_user(
        username="MarcelSoare",
        email="MarcelPitonul@example.com",
        password="pytest_authenticated_pass",
    )
    client.force_authenticate(user=user)
    return client
