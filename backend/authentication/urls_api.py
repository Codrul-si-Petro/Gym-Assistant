from django.urls import path

from .views import (
    api_change_password,
    api_delete_account,
    api_login,
    api_logout,
    api_password_reset_confirm,
    api_password_reset_request,
    api_signup,
    api_update_preferences,
    api_update_username,
    current_user,
)

urlpatterns = [
    path("login/", api_login, name="api_login"),
    path("signup/", api_signup, name="api_signup"),
    path("logout/", api_logout, name="api_logout"),
    path("current-user/", current_user, name="api_current_user"),
    path("delete-account/", api_delete_account, name="api_delete_account"),
    path("change-password/", api_change_password, name="api_change_password"),
    path("update-username/", api_update_username, name="api_update_username"),
    path("preferences/", api_update_preferences, name="api_update_preferences"),
    path("password-reset/", api_password_reset_request, name="api_password_reset_request"),
    path("password-reset/confirm/", api_password_reset_confirm, name="api_password_reset_confirm"),
]
