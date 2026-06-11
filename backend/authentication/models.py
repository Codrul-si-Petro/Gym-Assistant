from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for the app.

    Managed by Django migrations in the public schema. All other schemas/tables
    use Alembic (core) or dbt (dimensions).
    """

    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email_address = None

    # Let Django manage this table (in public schema)
    # Only core tables use Alembic with separate schemas
    preferred_unit = models.CharField(max_length=3, choices=[("KG", "KG"), ("LBS", "LBS")], default="KG")
