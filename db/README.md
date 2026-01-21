# Database Migrations

This project uses **Alembic** for database migrations with a multi-schema setup:

- `auth` schema: User authentication tables
- `core` schema: Application data tables (workouts, exercises, etc.)

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

## Schema Structure

### auth schema
- `users` - Custom user model
- `groups` - Permission groups
- `permissions` - Individual permissions
- `user_groups` - User-group relationships
- `user_permissions` - User-permission relationships
- `group_permissions` - Group-permission relationships

### core schema
- `dim_calendar` - Date dimension
- `dim_exercises` - Exercise dimension
- `dim_muscles` - Muscle dimension
- `dim_equipment` - Equipment dimension
- `dim_attachments` - Attachment dimension
- `exercise_muscle_bridge` - Exercise-muscle relationships
- `fact_workouts` - Workout fact table
