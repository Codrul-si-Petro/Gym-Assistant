from django.conf import settings
from django.db import models

from .custom_fields import DateForeignKey


# main tables
class Workouts(models.Model):

    workout_id = models.AutoField(primary_key=True, db_index=True)
    user= models.ForeignKey (
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            default=1
            )
    workout_number = models.PositiveIntegerField(auto_created=True)
    date = DateForeignKey(
            to="Calendar",
            on_delete=models.CASCADE,
            to_field="date_id",
            db_column="date_id",
            default="2025-01-01",
            )
    exercise = models.ForeignKey(
            to="Exercises",
            on_delete=models.CASCADE,
            default="1"
            )
    set_number = models.SmallIntegerField()
    repetitions = models.SmallIntegerField()
    load = models.DecimalField(max_digits=9, decimal_places=2)
    unit = models.TextField(default='KG')
    equipment = models.ForeignKey(
            to="Equipment",
            on_delete=models.CASCADE,
            default="1")
    attachment = models.ForeignKey(
            to="Attachments",
            on_delete=models.CASCADE,
            default="1")
    set_type = models.TextField(default='Working set')
    comments = models.TextField(default='N/A')
    workout_split = models.TextField(max_length=50)
    ta_created_at = models.DateTimeField(auto_now_add=True)
    ta_updated_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "fact_workouts"


class Exercises(models.Model):

    exercise_id = models.AutoField(primary_key=True, db_index=True)
    exercise_name = models.TextField(max_length=256)
    exercise_movement_type = models.TextField()
    ta_created_at = models.DateTimeField(auto_now_add=True)
    ta_updated_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "dim_exercises"


class Muscles(models.Model):

    muscle_id = models.AutoField(primary_key=True, db_index=True)
    muscle_name = models.TextField(max_length=256)
    muscle_group = models.TextField(max_length=20)
    ta_created_at = models.DateTimeField(auto_now_add=True)
    ta_updated_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "dim_muscles"


class Exercise_Muscle_Bridge(models.Model):

    exercise = models.ForeignKey(
            to="Exercises",
            on_delete=models.CASCADE,
            default="1")
    muscle = models.ForeignKey(
            to="Muscles",
            on_delete=models.CASCADE,
            default="1")
    muscle_role = models.TextField(default=None)
    ta_created_at = models.DateTimeField(auto_now_add=True)
    ta_updated_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "exercise_muscle_bridge"


class Equipment(models.Model):

    equipment_id = models.AutoField(primary_key=True, db_index=True)
    equipment_name = models.TextField()
    equipment_description = models.TextField()
    equipment_category = models.TextField()
    ta_created_at = models.DateTimeField(auto_now_add=True)
    ta_updated_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "dim_equipment"


class Attachments(models.Model):

    attachment_id = models.AutoField(primary_key=True, db_index=True)
    attachment_name = models.TextField()
    attachment_description = models.TextField()
    ta_created_at = models.DateTimeField(auto_now_add=True)
    ta_updated_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "dim_attachments"


class Calendar(models.Model):
    date_id = models.DateField(primary_key=True, db_index=True, default='1900-01-01')
    week_day = models.SmallIntegerField()
    day_number_in_month = models.SmallIntegerField()
    day_name_in_week = models.TextField()
    calendar_month_number = models.SmallIntegerField()
    calendar_month_name = models.TextField()
    calendar_year = models.SmallIntegerField()
    is_weekend = models.BooleanField()

    class Meta:
        db_table = "dim_calendar"
