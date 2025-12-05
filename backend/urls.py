"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Gym Assistant API",
      default_version='v1',
      description="API documentation for Gym Assistant",
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # API
    path('api/', include('core.urls_api')),

    # Swagger UI
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Authentication
    path('auth/', include('dj_rest_auth.urls')),  # login
    path('auth/', include('django.contrib.auth.urls')),  # pass reset 
    path('auth/registration/', include('dj_rest_auth.registration.urls')),   # sign up
    path('social/', include('allauth.socialaccount.providers.google.urls')),  # google login
    # include Authentication
    path('', include('authentication.urls')),

    # Home page
    path('', include('core.urls'))
]
