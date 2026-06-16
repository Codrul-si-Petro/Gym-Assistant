from pathlib import Path

from backend.core.analytics.crud.common import execute_sql

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def _youtube_embed_url(url: str | None) -> str | None:
    if not url:
        return None
    if "youtu.be/" in url:
        video_id = url.rsplit("/", 1)[-1].split("?")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "/embed/" in url:
        return url
    return None


def _group_glossary_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[int, dict] = {}
    order: list[int] = []

    for row in rows:
        exercise_id = row["exercise_id"]
        if exercise_id == -1:
            continue
        if exercise_id not in grouped:
            youtube_url = row.get("youtube_url")
            grouped[exercise_id] = {
                "exercise_id": exercise_id,
                "exercise_name": row["exercise_name"],
                "exercise_movement_type": row["exercise_movement_type"],
                "muscles": [],
                "youtube_url": youtube_url,
                "display_title": row.get("display_title"),
                "notes": row.get("notes"),
                "youtube_embed_url": _youtube_embed_url(youtube_url),
            }
            order.append(exercise_id)

        if row.get("muscle_id") is not None and row["muscle_id"] != -1:
            grouped[exercise_id]["muscles"].append(
                {
                    "muscle_id": row["muscle_id"],
                    "muscle_name": row["muscle_name"],
                    "muscle_role": row["muscle_role"],
                }
            )

    for exercise_id in order:
        grouped[exercise_id]["muscles"].sort(
            key=lambda m: (
                0 if (m.get("muscle_role") or "").lower() == "primary" else 1,
                m.get("muscle_name") or "",
            )
        )

    return [grouped[exercise_id] for exercise_id in order]


def _fetch_glossary(exercise_id: int | None) -> list[dict]:
    query = (SQL_DIR / "get_exercise_glossary.sql").read_text()
    rows = execute_sql(query, {"exercise_id": exercise_id})
    return _group_glossary_rows(rows)


def get_exercise_glossary_list() -> list[dict]:
    return _fetch_glossary(None)


def get_exercise_glossary(exercise_id: int) -> dict | None:
    rows = _fetch_glossary(exercise_id)
    return rows[0] if rows else None
