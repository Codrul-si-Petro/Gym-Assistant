from django.urls import path

from .views import current_user, login_page_view, login_success_view

urlpatterns = [
    path("login-success/", login_success_view, name="login_success"),
    path("login/", login_page_view, name="login"),
    path("auth/current-user-logged-in", current_user),
]
