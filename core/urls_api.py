from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
        WorkoutsViewSet,
        ExercisesViewSet,
        MusclesViewSet,
        AttachmentsViewSet
        )

router = DefaultRouter()
router.register(r'workouts', WorkoutsViewSet, basename='workouts')
router.register(r'exercises', ExercisesViewSet, basename='exercises')
router.register(r'attachments', AttachmentsViewSet, basename='attachments')
router.register(r'muscles', MusclesViewSet, basename='muscles')

urlpatterns = [
    path('api/', include(router.urls)),
]
