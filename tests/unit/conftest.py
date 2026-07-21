import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from backend.core.models import Attachments, Calendar, Equipment, Exercises

User = get_user_model()


@pytest.fixture
def dims(db):
    """First leaf rows of each dimension + a calendar date, skipping if unseeded."""
    exercises = list(Exercises.objects.filter(is_leaf=True).order_by("exercise_id")[:2])
    equipment = Equipment.objects.filter(is_leaf=True).order_by("equipment_id").first()
    attachment = Attachments.objects.filter(is_leaf=True).order_by("attachment_id").first()
    calendar = Calendar.objects.filter(date_id__gte="2025-01-01").order_by("date_id").first()
    if len(exercises) < 2 or equipment is None or attachment is None or calendar is None:
        pytest.skip("Dimension tables are not seeded in this database")
    return {
        "exercise": exercises[0].exercise_id,
        "exercise_alt": exercises[1].exercise_id,
        "equipment": equipment.equipment_id,
        "attachment": attachment.attachment_id,
        "date": calendar.date_id.isoformat(),
    }


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
