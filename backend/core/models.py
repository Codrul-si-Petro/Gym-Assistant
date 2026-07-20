"""
Core ORM models mirror tables in the `core` schema.

These models are unmanaged (`managed = False`). Schema changes belong in Alembic
(`db/alembic/versions/`), not Django migrations. Django only manages auth tables.
"""

from django.conf import settings
from django.db import models

from .custom_fields import DateForeignKey


class Workouts(models.Model):
    """Fact table for workout data. Managed by Alembic in core schema."""

    workout_id = models.AutoField(primary_key=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    workout_number = models.PositiveIntegerField(auto_created=True)
    date = DateForeignKey(
        to="Calendar",
        on_delete=models.CASCADE,
        to_field="date_id",
        db_column="date_id",
        default="2025-01-01",
    )
    exercise = models.ForeignKey(to="Exercises", on_delete=models.CASCADE, default="1")
    set_number = models.SmallIntegerField()
    repetitions = models.SmallIntegerField()
    load = models.DecimalField(max_digits=9, decimal_places=2)
    unit = models.TextField(default="KG")
    equipment = models.ForeignKey(to="Equipment", on_delete=models.CASCADE, default="1")
    attachment = models.ForeignKey(to="Attachments", on_delete=models.CASCADE, default="1")
    set_type = models.TextField(default="Working set")
    comments = models.TextField(default="N/A")
    workout_split = models.TextField(max_length=50)
    scenario = models.CharField(max_length=10, default="actuals")
    ta_created_at = models.DateTimeField(auto_now_add=True)
    ta_updated_at = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'core"."fact_workouts'


class Exercises(models.Model):
    """Dimension table for exercises. Managed by Alembic in core schema."""

    exercise_id = models.AutoField(primary_key=True, db_index=True)
    exercise_name = models.TextField(max_length=256)
    is_leaf = models.BooleanField()
    exercise_movement_type = models.TextField()
    ta_created_at = models.DateTimeField(auto_now_add=True)
    last_built = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'core"."dim_exercises'


class Muscles(models.Model):
    """Dimension table for muscles. Managed by dbt in core schema."""

    muscle_id = models.AutoField(primary_key=True, db_index=True)
    muscle_name = models.TextField(max_length=256)
    muscle_parent_id = models.IntegerField(null=True)
    is_leaf = models.BooleanField()
    ta_created_at = models.DateTimeField(auto_now_add=True)
    last_built = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'core"."dim_muscles'


class ExerciseMedia(models.Model):
    """Optional media metadata for exercises (YouTube demos, notes).

    Schema: dbt model `exercise_media` in `db/transformation/models/core/`.
    exercise_id references dim_exercises logically (no DB FK; dbt rebuilds dims).
    """

    media_id = models.AutoField(primary_key=True, db_index=True)
    exercise = models.OneToOneField(
        to="Exercises",
        on_delete=models.CASCADE,
        db_column="exercise_id",
        related_name="media",
    )
    youtube_url = models.TextField()
    display_title = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    ta_created_at = models.DateTimeField(auto_now_add=True)
    ta_updated_at = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'core"."exercise_media'


class AttachmentMedia(models.Model):
    """Optional image metadata for attachments (glossary reference photos).

    Schema: dbt model `attachment_media` in `db/transformation/models/core/`.
    attachment_id references dim_attachments logically (no DB FK; dbt rebuilds dims).
    """

    media_id = models.AutoField(primary_key=True, db_index=True)
    attachment = models.OneToOneField(
        to="Attachments",
        on_delete=models.CASCADE,
        db_column="attachment_id",
        related_name="media",
    )
    image_url = models.TextField()
    display_title = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    ta_created_at = models.DateTimeField(auto_now_add=True)
    ta_updated_at = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'core"."attachment_media'


class Exercise_Muscle_Bridge(models.Model):
    """Bridge table linking exercises to muscles. Managed by dbt in core schema."""

    exercise = models.ForeignKey(to="Exercises", on_delete=models.CASCADE, default="1")
    muscle = models.ForeignKey(to="Muscles", on_delete=models.CASCADE, default="1")
    muscle_role = models.TextField(default=None)
    last_built = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'core"."exercise_muscle_bridge'


class Equipment(models.Model):
    """Dimension table for equipment. Managed by dbt in core schema."""

    equipment_id = models.AutoField(primary_key=True, db_index=True)
    equipment_name = models.TextField()
    equipment_description = models.TextField()
    equipment_category = models.TextField()
    is_leaf = models.BooleanField()
    ta_created_at = models.DateTimeField(auto_now_add=True)
    last_built = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'core"."dim_equipment'


class EquipmentMedia(models.Model):
    """Optional image metadata for equipment (glossary reference photos).

    Schema: dbt model `equipment_media` in `db/transformation/models/core/`.
    equipment_id references dim_equipment logically (no DB FK; dbt rebuilds dims).
    """

    media_id = models.AutoField(primary_key=True, db_index=True)
    equipment = models.OneToOneField(
        to="Equipment",
        on_delete=models.CASCADE,
        db_column="equipment_id",
        related_name="media",
    )
    image_url = models.TextField()
    display_title = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    ta_created_at = models.DateTimeField(auto_now_add=True)
    ta_updated_at = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'core"."equipment_media'


class Attachments(models.Model):
    """Dimension table for attachments. Managed by Alembic in core schema."""

    attachment_id = models.AutoField(primary_key=True, db_index=True)
    attachment_name = models.TextField()
    attachment_description = models.TextField()
    is_leaf = models.BooleanField()
    ta_created_at = models.DateTimeField(auto_now_add=True)
    last_built = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'core"."dim_attachments'


class Calendar(models.Model):
    """Dimension table for calendar/dates. Managed by nothing actually."""

    date_id = models.DateField(primary_key=True, db_index=True, default="1900-01-01")
    week_day = models.SmallIntegerField()
    day_number_in_month = models.SmallIntegerField()
    day_number_in_week = models.SmallIntegerField()
    calendar_month_number = models.SmallIntegerField()
    calendar_month_name = models.TextField()
    calendar_year = models.SmallIntegerField()
    is_weekend = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'core"."dim_calendar'
