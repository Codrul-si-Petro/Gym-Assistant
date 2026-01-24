from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

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
    # Swagger UI
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # Authentication
    path("auth/", include("django.contrib.auth.urls")),  # login/password reset
    path("accounts/", include("allauth.urls")),  # allauth (signup, login, social)
    path("social/", include("allauth.socialaccount.providers.google.urls")),  # google login
    # include Authentication
    path("", include("backend.authentication.urls")),
    # Home page
    path("", include("backend.core.urls")),
]
