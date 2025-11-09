from django.contrib.auth.models import AbstractUser, Group
from django.db import models

def create_default_groups():
    admin_group = Group.objects.get_or_create(name="admin")
    user_group = Group.objects.get_or_create(name="user")


class User(AbstractUser):
    """
    This will be the standard user of the app.
    """
    first_name = None
    last_name = None



