import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
def test_rest_days_authenticated_shape(authenticated_client):
    response = authenticated_client.get("/api/v1/rest-days", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "count" in response.data
    assert "results" in response.data
    assert isinstance(response.data["results"], list)
    assert response.data["count"] == len(response.data["results"])
    for row in response.data["results"]:
        assert set(row.keys()) >= {"date_id"}


@pytest.mark.django_db
def test_rest_days_unauthenticated_returns_401(api_client):
    response = api_client.get("/api/v1/rest-days", format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_favourite_exercises_authenticated_shape(authenticated_client):
    response = authenticated_client.get("/api/v1/favourite-exercises", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert isinstance(response.data["results"], list)
    for row in response.data["results"]:
        assert set(row.keys()) >= {"exercise_id", "exercise_name", "counter", "rank"}


@pytest.mark.django_db
def test_favourite_exercises_invalid_date_range_returns_400(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/favourite-exercises",
        {"start_date": "2025-12-01", "end_date": "2025-01-01"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_favourite_exercise_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/favourite-exercises", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert isinstance(response.data["results"], list)


@pytest.mark.django_db
def test_total_volume_authenticated_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/total-volume", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data


@pytest.mark.django_db
def test_total_volume_authenticated_shape(authenticated_client):
    response = authenticated_client.get("/api/v1/total-volume", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert len(response.data["results"]) >= 1
    for row in response.data["results"]:
        assert set(row.keys()) >= {
            "exercise_id",
            "exercise_name",
            "is_leaf",
            "total_volume_kg",
            "rank",
        }


# TODO: do not forget to fix this test to get parent_id returning results
@pytest.mark.django_db
def test_total_volume_with_parent_id_returns_results(authenticated_client):
    user_id = User.objects.get(username="MarcelSoare").pk
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT exercise_id FROM analytics.total_daily_volume
            WHERE user_id = %s
            ORDER BY date_id DESC
            LIMIT 1
            """,
            [user_id],
        )
        row = cursor.fetchone()
        if not row:
            pytest.skip("No seeded analytics row for user")
        exercise_id = row[0]

        cursor.execute(
            """
            SELECT parent_id
            FROM core.dimension_hierarchies
            WHERE dimension = 'exercise' AND current_id = %s
            """,
            [exercise_id],
        )
        prow = cursor.fetchone()
        if not prow or prow[0] is None:
            pytest.skip("Seeded exercise has no parent — cannot drill with parent_id")

        parent_id = prow[0]

    response = authenticated_client.get(
        "/api/v1/total-volume",
        {"parent_id": parent_id},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert isinstance(response.data["results"], list)
    assert len(response.data["results"]) >= 1
