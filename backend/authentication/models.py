from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model for the app.
    Managed by Django in public schema.
    """

    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email_address = None  # type: ignore[assignment]

    # Let Django manage this table (in public schema)
    # Only core tables use Alembic with separate schemas
