from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0006_add_update_cascade_to_socialaccount"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="preferred_unit",
            field=models.CharField(
                choices=[("KG", "KG"), ("LBS", "LBS")],
                default="KG",
                max_length=3,
            ),
        ),
    ]
