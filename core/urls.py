from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
        homepageView
        )

router = DefaultRouter()

urlpatterns = [
    path('', homepageView, name='home')
]
