from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from backend.authentication.views import (
    CustomAllauthLoginView,
    CustomAllauthSignupView,
    CustomPasswordChangeView,
    CustomPasswordResetCompleteView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetDoneView,
    CustomPasswordResetView,
)

from .views import WorkoutFormView, homepageView

schema_view = get_schema_view(
    openapi.Info(
        title="Gym Assistant API",
        default_version="v1",
        description="API documentation for Gym Assistant",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path("admin/", admin.site.urls),
    # API
    path("api/", include("backend.core.urls_api")),
    path("api/", include("backend.core.analytics.urls")),
    path("api/auth/", include("backend.authentication.urls_api")),
    # JWT Token stuff
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Swagger UI
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # Authentication - Override Django's built-in password reset views with custom templates
    path("auth/password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("auth/password_reset/done/", CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("auth/reset/<uidb64>/<token>/", CustomPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("auth/reset/done/", CustomPasswordResetCompleteView.as_view(), name="password_reset_complete"),
    # Override django-allauth views with custom templates
    path("accounts/login/", CustomAllauthLoginView.as_view(), name="account_login"),
    path("accounts/signup/", CustomAllauthSignupView.as_view(), name="account_signup"),
    # Include remaining allauth URLs (logout, email verification, etc.)
    path("accounts/password/change/", CustomPasswordChangeView.as_view(), name="account_change_password"),
    path("accounts/", include("allauth.urls")),
    path("social/", include("allauth.socialaccount.providers.google.urls")),  # google login
    # include Authentication
    path("", include("backend.authentication.urls")),
    # Home page
    path("", homepageView, name="home"),
]
