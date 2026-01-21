from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AttachmentsViewSet, ExercisesViewSet, MusclesViewSet, WorkoutsViewSet

router = DefaultRouter()
router.register(r'workouts', WorkoutsViewSet, basename='workouts')
router.register(r'exercises', ExercisesViewSet, basename='exercises')
router.register(r'attachments', AttachmentsViewSet, basename='attachments')
router.register(r'muscles', MusclesViewSet, basename='muscles')

urlpatterns = [
    path('', include(router.urls)),
]
