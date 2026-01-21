from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    This will be the standard user of the app.
    """

    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
