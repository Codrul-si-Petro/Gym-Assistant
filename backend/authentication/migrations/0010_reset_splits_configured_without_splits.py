# Reset onboarding flag for users with no splits (e.g. after a manual TRUNCATE).

from django.db import migrations


def reset_configured_without_splits(apps, schema_editor):
    """If a user has zero split rows, they have not finished onboarding with a real list.

    Opt-out still sets workout_splits_configured=True with an empty list; this
    data repair re-opens the modal for empty-split users once (including after
    TRUNCATE public.authentication_userworkoutsplit). Users who opt out again
    stay configured.
    """
    User = apps.get_model("authentication", "User")
    UserWorkoutSplit = apps.get_model("authentication", "UserWorkoutSplit")
    user_ids_with_splits = UserWorkoutSplit.objects.order_by().values_list("user_id", flat=True).distinct()
    User.objects.exclude(id__in=user_ids_with_splits).update(workout_splits_configured=False)


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0009_user_workout_splits_configured"),
    ]

    operations = [
        migrations.RunPython(reset_configured_without_splits, migrations.RunPython.noop),
    ]
