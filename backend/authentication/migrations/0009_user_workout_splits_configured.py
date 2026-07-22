# Generated manually for workout_splits_configured onboarding flag

from django.db import migrations, models


def mark_users_with_splits_configured(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    UserWorkoutSplit = apps.get_model("authentication", "UserWorkoutSplit")
    user_ids = UserWorkoutSplit.objects.order_by().values_list("user_id", flat=True).distinct()
    User.objects.filter(id__in=user_ids).update(workout_splits_configured=True)


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0008_userworkoutsplit"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="workout_splits_configured",
            field=models.BooleanField(
                default=False,
                help_text="True once the user set splits or explicitly opted out during onboarding.",
            ),
        ),
        migrations.RunPython(mark_users_with_splits_configured, migrations.RunPython.noop),
    ]
