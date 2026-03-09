import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestRestDaysEndpoint(TestCase):
    def setUp(self):  # must be named like Pascalcase otherwise this will fail on force_authenticate
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analytics_test_user",
            email="analytics@example.com",
            password="testpass123",
        )

    def test_rest_days_authenticated_returns_200(self):
        url = "/api/v1/rest-days"
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)

    def test_rest_days_unauthenticated_returns_401(self):
        url = "/api/v1/rest-days"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
class TestFavouriteExercisesEndpoint(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analytics_test_user",
            email="analytics@example.com",
            password="gigelmarcel33",
        )

    def test_favourite_exercise_returns_200(self):
        url = "/api/v1/favourite-exercises"
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
