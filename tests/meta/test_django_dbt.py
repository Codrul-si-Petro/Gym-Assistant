"""
This test is put in place because we still rely on Django ORM which relies on its' models.
Our core dimensions are dbt managed and Django-managed: false but the ORM can break if
I move dbt models to another schema or change their name.
"""

from backend.core.models import (
    Attachments,
    Calendar,
    Equipment,
    Exercise_Muscle_Bridge,
    Exercises,
    Muscles,
)
from tests.helpers import db_cursor


def parse_table_name(db_table: str):
    cleaned = db_table.replace('"', "")
    schema, table = cleaned.split(".")
    return schema, table


# yes this is slop
def format_failure(model_name: str, result: dict) -> str:
    lines = [f"\n❌ {model_name} failed schema check"]

    if result["missing_attributes"]:
        lines.append("  Missing columns:")
        for col in result["missing_attributes"]:
            lines.append(f"    - {col}")

    if result["mismatches"]:
        lines.append("  Type mismatches:")
        for m in result["mismatches"]:
            lines.append(
                f"    - {m['column']}: "
                f"{m['django_type']} -> "
                f"expected {m['expected_pg_type']}, got {m['actual_pg_type']}"
            )

    return "\n".join(lines)


def get_django_model(model):
    return {
        "table": model._meta.db_table,
        "columns": {f.column: f.get_internal_type() for f in model._meta.fields},
    }


def get_pg_table(schema: str, table: str):
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position;
            """,
            [schema, table],
        )
        rows = cur.fetchall()

        return {
            "exists": bool(rows),
            "columns": {r[0]: r[1] for r in rows},
        }


def compare_models(django_model: dict, pg_model: dict):
    django_attributes = django_model["columns"]
    pg_attributes = pg_model["columns"]

    missing_attributes = set(django_attributes) - set(pg_attributes)

    type_translation = {
        "AutoField": "integer",
        "BigAutoField": "integer",
        "IntegerField": "integer",
        "SmallIntegerField": "smallint",
        "TextField": "text",
        "CharField": "text",
        "BooleanField": "boolean",
        "DateField": "date",
        "DateTimeField": "timestamp with time zone",
        "ForeignKey": "integer",
    }

    mismatches = []

    for attr in set(django_attributes) & set(pg_attributes):
        django_type = django_attributes[attr]
        expected_pg_type = type_translation.get(django_type)
        actual_pg_type = pg_attributes[attr]

        if expected_pg_type != actual_pg_type:
            mismatches.append(
                {
                    "column": attr,
                    "django_type": django_type,
                    "expected_pg_type": expected_pg_type,
                    "actual_pg_type": actual_pg_type,
                }
            )

    return {
        "ok": not missing_attributes and not mismatches,
        "missing_attributes": list(missing_attributes),
        "mismatches": mismatches,
    }


def test_django_pg_models_match():
    models = [
        Exercises,
        Attachments,
        Equipment,
        Calendar,
        Exercise_Muscle_Bridge,
        Muscles,
    ]

    failures = []

    for model in models:
        django = get_django_model(model)

        schema, table = parse_table_name(django["table"])
        pg = get_pg_table(schema, table)
        result = compare_models(django, pg)

        if not result["ok"]:
            failures.append((model.__name__, result))

    if failures:
        message = "\n".join(format_failure(name, result) for name, result in failures)
        raise AssertionError(message)
