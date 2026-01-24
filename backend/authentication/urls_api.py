from django.urls import path

from .views import api_delete_account, api_login, api_logout, api_signup, current_user

urlpatterns = [
    path("login/", api_login, name="api_login"),
    path("signup/", api_signup, name="api_signup"),
    path("logout/", api_logout, name="api_logout"),
    path("current-user/", current_user, name="api_current_user"),
    path("delete-account/", api_delete_account, name="api_delete_account"),
]
