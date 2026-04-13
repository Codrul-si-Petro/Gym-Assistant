from rest_framework import status


def test_rest_days_unauthenticated_returns_401(api_client):
    response = api_client.get("/api/v1/rest-days", format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_favourite_exercises_invalid_date_range_returns_400(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/favourite-exercises",
        {"start_date": "2025-12-01", "end_date": "2025-01-01"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_favourite_exercise_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/favourite-exercises", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert isinstance(response.data["results"], list)


def test_total_volume_authenticated_returns_200(authenticated_client):
    response = authenticated_client.get("/api/v1/total-volume", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data


def test_total_volume_with_parent_id_returns_results(authenticated_client):
    response = authenticated_client.get(
        "/api/v1/total-volume",
        {"parent_id": 48},  # hardcoded because this uses the long-lived E2E test user with bootstrapped
        format="json",  # seeded data which should not change. if this fails, check seeded data
    )
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    for row in response.data["results"]:
        assert set(row.keys()) == {
            "exercise_id",
            "exercise_name",
            "is_leaf",
            "total_volume_kg",
            "rank",
        }
