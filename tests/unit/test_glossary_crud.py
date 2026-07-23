"""Unit tests for glossary grouping and YouTube embed URL helpers (no DB)."""

from backend.core.glossary.crud.crud import _group_glossary_rows, _youtube_embed_url


def test_youtube_embed_url_youtu_be():
    assert _youtube_embed_url("https://youtu.be/abc123XYZ") == "https://www.youtube.com/embed/abc123XYZ"


def test_youtube_embed_url_youtu_be_strips_query():
    assert _youtube_embed_url("https://youtu.be/abc123XYZ?si=token") == "https://www.youtube.com/embed/abc123XYZ"


def test_youtube_embed_url_watch_v_param():
    assert (
        _youtube_embed_url("https://www.youtube.com/watch?v=abc123XYZ&t=30")
        == "https://www.youtube.com/embed/abc123XYZ"
    )


def test_youtube_embed_url_already_embed():
    url = "https://www.youtube.com/embed/abc123XYZ"
    assert _youtube_embed_url(url) == url


def test_youtube_embed_url_none_and_unknown():
    assert _youtube_embed_url(None) is None
    assert _youtube_embed_url("") is None
    assert _youtube_embed_url("https://example.com/video") is None


def test_group_glossary_rows_skips_placeholder_and_sorts_primary_first():
    rows = [
        {
            "exercise_id": -1,
            "exercise_name": "None",
            "exercise_movement_type": "N/A",
            "muscle_id": -1,
            "muscle_name": "None",
            "muscle_role": None,
            "youtube_url": None,
            "display_title": None,
            "notes": None,
        },
        {
            "exercise_id": 10,
            "exercise_name": "Bench Press",
            "exercise_movement_type": "Push",
            "muscle_id": 2,
            "muscle_name": "Triceps",
            "muscle_role": "secondary",
            "youtube_url": "https://youtu.be/bench1",
            "display_title": "Bench",
            "notes": None,
        },
        {
            "exercise_id": 10,
            "exercise_name": "Bench Press",
            "exercise_movement_type": "Push",
            "muscle_id": 1,
            "muscle_name": "Chest",
            "muscle_role": "primary",
            "youtube_url": "https://youtu.be/bench1",
            "display_title": "Bench",
            "notes": None,
        },
        {
            "exercise_id": 10,
            "exercise_name": "Bench Press",
            "exercise_movement_type": "Push",
            "muscle_id": -1,
            "muscle_name": "None",
            "muscle_role": None,
            "youtube_url": "https://youtu.be/bench1",
            "display_title": "Bench",
            "notes": None,
        },
    ]

    grouped = _group_glossary_rows(rows)
    assert len(grouped) == 1
    entry = grouped[0]
    assert entry["exercise_id"] == 10
    assert entry["youtube_embed_url"] == "https://www.youtube.com/embed/bench1"
    assert [m["muscle_name"] for m in entry["muscles"]] == ["Chest", "Triceps"]
    assert entry["muscles"][0]["muscle_role"] == "primary"
