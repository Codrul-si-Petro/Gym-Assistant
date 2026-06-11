from rest_framework import status


def test_get_exercises(authenticated_client):
    response = authenticated_client.get("/api/exercises/", format="json")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list), "Non-paginated list should be a JSON array"

    item = data[0]
    assert set(item.keys()) >= {
        "exercise_id",
        "exercise_name",
        "exercise_movement_type",
    }, "Missing keys from the response"
    assert isinstance(item["exercise_id"], int)
    assert isinstance(item["exercise_name"], str)
    assert isinstance(item["exercise_movement_type"], str)


def test_get_muscles(authenticated_client):
    response = authenticated_client.get("/api/muscles/", format="json")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list), "Non-paginated list should be a JSON array"

    item = data[0]
    assert set(item.keys()) >= {
        "muscle_id",
        "muscle_name",
    }, "Missing keys from the response"
    assert isinstance(item["muscle_id"], int)
    assert isinstance(item["muscle_name"], str)


def test_get_attachments(authenticated_client):
    response = authenticated_client.get("/api/attachments/", format="json")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list), "Non-paginated list should be a JSON array"

    item = data[0]
    assert set(item.keys()) >= {
        "attachment_id",
        "attachment_name",
        "attachment_description",
    }, "Missing keys from the response"
    assert isinstance(item["attachment_id"], int)
    assert isinstance(item["attachment_name"], str)


def test_get_exercises_glossary(authenticated_client):
    response = authenticated_client.get("/api/exercises/glossary/", format="json")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    if not data:
        return

    item = data[0]
    assert set(item.keys()) >= {
        "exercise_id",
        "exercise_name",
        "exercise_movement_type",
        "muscles",
        "youtube_url",
        "youtube_embed_url",
    }
    assert isinstance(item["muscles"], list)


def test_get_exercise_glossary_detail(authenticated_client):
    listing = authenticated_client.get("/api/exercises/", format="json")
    assert listing.status_code == status.HTTP_200_OK
    exercises = listing.json()
    assert exercises, "Need at least one exercise to test the glossary detail endpoint"

    exercise_id = exercises[0]["exercise_id"]
    response = authenticated_client.get(f"/api/exercises/{exercise_id}/glossary/", format="json")
    assert response.status_code == status.HTTP_200_OK

    item = response.json()
    assert item["exercise_id"] == exercise_id
    assert set(item.keys()) >= {
        "exercise_id",
        "exercise_name",
        "exercise_movement_type",
        "muscles",
        "youtube_url",
        "youtube_embed_url",
    }
    assert isinstance(item["muscles"], list)


def test_get_equipment(authenticated_client):
    response = authenticated_client.get("/api/equipment/", format="json")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list), "Non-paginated list should be a JSON array"

    item = data[0]
    assert set(item.keys()) >= {
        "equipment_id",
        "equipment_name",
        "equipment_description",
    }, "Missing keys from the response"
    assert isinstance(item["equipment_id"], int)
    assert isinstance(item["equipment_name"], str)
