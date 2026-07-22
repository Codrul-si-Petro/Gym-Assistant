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
    workout_splits_configured = models.BooleanField(
        default=False,
        help_text="True once the user set splits or explicitly opted out during onboarding.",
    )


class UserWorkoutSplit(models.Model):
    """User-defined workout split labels (optional enum for plans / logging)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workout_splits")
    name = models.CharField(max_length=50)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="uniq_user_workout_split_name"),
        ]

    def __str__(self) -> str:
        return self.name
