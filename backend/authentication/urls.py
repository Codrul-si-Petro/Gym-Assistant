from django.urls import path

from .views import current_user

urlpatterns = [
    path("auth/current-user-logged-in", current_user),
]
