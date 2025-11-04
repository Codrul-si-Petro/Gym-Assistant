from django.db import models

# define the schema with db table and some inheritance magic

# main tables
class Workouts(models.Model):

    workout_id = models.AutoField(primary_key=True, db_index=True)
    workout_number = models.PositiveIntegerField(auto_created=True)
    date_id = models.ForeignKey(to="Calendar", on_delete=models.CASCADE)
    exercise_id = models.ForeignKey(to="Exercises", on_delete=models.CASCADE)
    repetitions = models.SmallIntegerField()
    load = models.DecimalField(max_digits=9, decimal_places=2)
    unit = models.TextField()
    equipment_id = models.ForeignKey(to="Equipment", on_delete=models.CASCADE)
    attachment_id = models.ForeignKey(to="Attachments", on_delete=models.CASCADE)
    set_type = models.TextField()
    comments = models.TextField()
    workout_split = models.TextField(max_length=50)
    ta_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workouts"


class Exercises(models.Model):

    exercise_id = models.AutoField(primary_key=True, db_index=True)
    exercise_name = models.TextField(max_length=256)
    exercise_movement_type = models.TextField()
    ta_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "exercises"

class Muscles(models.Model):

    muscle_id = models.AutoField(primary_key=True, db_index=True)
    muscle_name = models.TextField(max_length=256)
    muscle_group = models.TextField(max_length=20)
    ta_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "muscles"

class Exercise_Muscle_Bridge(models.Model):

    exercise_id = models.ForeignKey(to="Exercises", on_delete=models.CASCADE)
    muscle_id = models.ForeignKey(to="Muscles", on_delete=models.CASCADE)
    ta_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "exercise_muscle_bridge"

class Equipment(models.Model):

    equipment_id = models.AutoField(primary_key=True, db_index=True)
    equipment_name = models.TextField()
    equipment_description = models.TextField()
    equipment_category = models.TextField()
    ta_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "equipment"


class Attachments(models.Model):

    attachment_id = models.AutoField(primary_key=True, db_index=True)
    attachment_name = models.TextField()
    attachment_description = models.TextField()
    ta_created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attachments"

class Calendar(models.Model):

    date_id = models.DateField()
    week_day = models.TextField()
    day_number_in_month = models.SmallIntegerField()
    day_name_in_week = models.SmallIntegerField()
    calendar_month_number = models.SmallIntegerField()
    calendar_month_name = models.TextField()
    calendar_year = models.SmallIntegerField()
    is_weekend = models.BooleanField()
    class Meta:
        db_table = "calendar"


