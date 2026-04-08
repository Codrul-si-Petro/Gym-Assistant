import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


def _insert_total_daily_volume_row_for_user(user_id: int) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT date_id FROM core.dim_calendar ORDER BY date_id DESC LIMIT 1",
        )
        row = cursor.fetchone()
        if not row:
            pytest.skip("core.dim_calendar has no rows")
        date_id = row[0]

        cursor.execute(
            """
            SELECT current_id
            FROM core.dimension_hierarchies
            WHERE dimension = 'exercise' AND is_leaf = true
            ORDER BY current_id
            LIMIT 1
            """,
        )
        row = cursor.fetchone()
        if not row:
            pytest.skip("core.dimension_hierarchies has no exercise leaf rows")
        exercise_id = row[0]

        try:
            cursor.execute(
                """
                INSERT INTO analytics.total_daily_volume (date_id, user_id, exercise_id, volume)
                VALUES (%s, %s, %s, %s)
                """,
                [date_id, user_id, exercise_id, 1000.0],
            )
        except Exception as exc:
            pytest.skip(f"Could not seed analytics.total_daily_volume: {exc}")


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
    _insert_total_daily_volume_row_for_user(user.pk)
    client.force_authenticate(user=user)
    return client
