# Database Migrations

This project uses **Alembic** for database migrations with a multi-schema setup:

- `core.fact_workouts`: Only the fact table is Alembic managed right now. Other dim_tables are managed by dbt + seeds. 
- `everything else`: Managed by dbt or Django's migrations service

## Setup

Make sure you have your environment loaded:

```bash
source utils/load django dev
```

## Running Migrations

```bash
cd db
alembic upgrade head
```

## Creating New Migrations

```bash
cd db
alembic revision -m "description of changes"
```

Then edit the generated file in `alembic/versions/`.

## Rollback

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade 002

# Rollback all
alembic downgrade base
```

## Check Current Version

```bash
alembic current
```

## View Migration History

```bash
alembic history
```

