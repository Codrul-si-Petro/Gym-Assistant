from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from backend.authentication.decorators import staff_sso_required
from backend.authentication.views import redirect_to_frontend_login, redirect_to_frontend_signup

from .views import homepageView, sentry_debug

schema_view = get_schema_view(
    openapi.Info(
        title="Gym Assistant API",
        default_version="v1",
        description="API documentation for Gym Assistant",
    ),
    public=True,
    permission_classes=[permissions.IsAdminUser],
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
    # Swagger UI (staff-only via Google SSO)
    path(
        "swagger/",
        staff_sso_required(schema_view.with_ui("swagger", cache_timeout=0)),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        staff_sso_required(schema_view.with_ui("redoc", cache_timeout=0)),
        name="schema-redoc",
    ),
    # Redirect legacy Django auth entry points to static frontend
    path("accounts/login/", redirect_to_frontend_login, name="account_login"),
    path("accounts/signup/", redirect_to_frontend_signup, name="account_signup"),
    # allauth internals (social callbacks, logout, etc.)
    path("accounts/", include("allauth.urls")),
    path("social/", include("allauth.socialaccount.providers.google.urls")),  # google login
    # include Authentication
    path("", include("backend.authentication.urls")),
    # Sentry smoke test (404 when DEBUG=False)
    path("sentry-debug/", sentry_debug),
    # Home page
    path("", homepageView, name="home"),
]
