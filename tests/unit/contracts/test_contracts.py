import pytest
from rest_framework import status


@pytest.mark.django_db
def test_get_exercises(authenticated_client):
    response = authenticated_client.get("/api/exercises/", format="json")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list), "Non-paginated list should be a JSON array"

    if len(data) == 0:
        pytest.skip("No exercises in DB; seed data if you need non-empty assertions")

    item = data[0]
    assert set(item.keys()) >= {
        "exercise_id",
        "exercise_name",
        "exercise_movement_type",
    }, "Missing keys from the response"
    assert isinstance(item["exercise_id"], int)
    assert isinstance(item["exercise_name"], str)
    assert isinstance(item["exercise_movement_type"], str)


@pytest.mark.django_db
def test_get_muscles(authenticated_client):
    response = authenticated_client.get("/api/muscles/", format="json")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list), "Non-paginated list should be a JSON array"

    if len(data) == 0:
        pytest.skip("No exercises in DB; seed data if you need non-empty assertions")

    item = data[0]
    assert set(item.keys()) >= {
        "muscle_id",
        "muscle_name",
    }, "Missing keys from the response"
    assert isinstance(item["muscle_id"], int)
    assert isinstance(item["muscle_name"], str)


@pytest.mark.django_db
def test_get_attachments(authenticated_client):
    response = authenticated_client.get("/api/attachments/", format="json")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list), "Non-paginated list should be a JSON array"

    if len(data) == 0:
        pytest.skip("No exercises in DB; seed data if you need non-empty assertions")

    item = data[0]
    assert set(item.keys()) >= {
        "attachment_id",
        "attachment_name",
        "attachment_description",
    }, "Missing keys from the response"
    assert isinstance(item["attachment_id"], int)
    assert isinstance(item["attachment_name"], str)


@pytest.mark.django_db
def test_get_equipment(authenticated_client):
    response = authenticated_client.get("/api/equipment/", format="json")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list), "Non-paginated list should be a JSON array"

    if len(data) == 0:
        pytest.skip("No exercises in DB; seed data if you need non-empty assertions")

    item = data[0]
    assert set(item.keys()) >= {
        "equipment_id",
        "equipment_name",
        "equipment_description",
    }, "Missing keys from the response"
    assert isinstance(item["equipment_id"], int)
    assert isinstance(item["equipment_name"], str)
