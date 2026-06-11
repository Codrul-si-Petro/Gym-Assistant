# Database Migrations

This project splits schema ownership across three tools:

| Layer | Tool | What it manages |
|-------|------|-----------------|
| Auth | **Django migrations** | `public.authentication_user` and allauth-related FK fixes (`backend/authentication/migrations/`) |
| Core facts + app metadata | **Alembic** | `core.fact_workouts`, `core.exercise_media`, and other core tables added for the app |
| Dimensions + analytics | **dbt + seeds** | `core.dim_*`, bridges, hierarchies, analytics models |

Django is configured to **ignore** core app migrations via `MIGRATION_MODULES = {"core": None}` in `backend/settings.py`. Core models use `managed = False` and must not be created with `makemigrations`.

## Setup

```bash
source utils/load django dev
```

## Auth migrations (Django only)

From project root:

```bash
python manage.py makemigrations authentication
python manage.py migrate
```

Do **not** run `makemigrations` for `core`.

## Core migrations (Alembic)

```bash
cd db
alembic upgrade head
```

### Creating a new core migration

Prefer explicit revision files over autogenerate for tables outside Alembic metadata stubs:

```bash
cd db
alembic revision -m "description of changes"
```

Edit the generated file in `alembic/versions/`, then apply:

```bash
alembic upgrade head
```

Example: `006_exercise_media.py` adds `core.exercise_media` for glossary YouTube links.

Note: dbt-managed dimension tables (`dim_exercises`, etc.) may not have database-level
primary key constraints. Alembic tables that reference dimensions use logical `exercise_id`
columns with unique indexes instead of foreign keys.

## Rollback

```bash
cd db
alembic downgrade -1
alembic downgrade 006
alembic downgrade base
```

## Check status

```bash
cd db
alembic current
alembic history
```
