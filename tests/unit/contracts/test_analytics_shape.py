from rest_framework import status


def test_rest_days_authenticated_shape(authenticated_client):
    response = authenticated_client.get("/api/v1/rest-days", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "count" in response.data
    assert "results" in response.data
    assert isinstance(response.data["results"], list)
    assert response.data["count"] == len(response.data["results"])
    for row in response.data["results"]:
        assert set(row.keys()) >= {"date_id"}


def test_favourite_exercises_authenticated_shape(authenticated_client):
    response = authenticated_client.get("/api/v1/favourite-exercises", format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert isinstance(response.data["results"], list)
    for row in response.data["results"]:
        assert set(row.keys()) >= {"exercise_id", "exercise_name", "counter", "rank"}


def test_total_volume_authenticated_shape(authenticated_client):
    response = authenticated_client.get("/api/v1/total-volume", format="json")
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
