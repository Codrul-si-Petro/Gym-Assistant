from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import create_test_user

BASE_URL = "/api/auth"

User = get_user_model()


class AuthenticationAPITestCase(TestCase):
    """
    Test cases for authentication API endpoints.
    This class is nice because it uses Django internals and cleans resources after itself.
    """

    def setUp(self):
        """Set up test client and test user."""
        self.client = APIClient()
        self.test_user = create_test_user("MircelGagiul360", "testpass123femei")
        # Track users created during tests for cleanup
        self.created_users = [self.test_user]

    def tearDown(self):
        """Clean up test data after each test."""
        # No cleanup needed - Django's test framework automatically cleans up the test database
        # This avoids CASCADE delete issues with core schema tables that don't exist in test DB
        pass

    def test_login_success_returns_200(self):
        """Test that successful login returns 200 status code."""
        url = f"{BASE_URL}/login/"
        # this password has to be hardcoded. MUST match what the user created in the helper is
        data = {"username": "MircelGagiul360", "password": "testpass123femei"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("username", response.data)
        self.assertIn("email", response.data)
        self.assertIn("id", response.data)
        self.assertIn("message", response.data)

    def test_signup_success_returns_201(self):
        """Test that successful signup returns 201 status code."""
        url = f"{BASE_URL}/signup/"

        data = {
            "username": "MircelGagiul3590",
            "email": "MircelRekinu360@yahoo.com",
            "password1": "testpass123femei",
            "password2": "testpass123femei",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("username", response.data)
        self.assertIn("email", response.data)
        self.assertIn("id", response.data)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["username"], "MircelGagiul3590")
        # Verify user was created
        self.assertTrue(User.objects.filter(username="MircelGagiul3590").exists())
        # Track for cleanup
        new_user = User.objects.get(username="MircelGagiul3590")
        self.created_users.append(new_user)

    def test_logout_success_returns_200(self):
        """Test that successful logout returns 200 status code."""
        url = f"{BASE_URL}/logout/"
        # Login first
        self.client.force_authenticate(user=self.test_user)
        response = self.client.post(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Logout successful")

    def test_current_user_authenticated_returns_200(self):
        """Test that current user endpoint returns 200 for authenticated user."""
        url = f"{BASE_URL}/current-user/"
        self.client.force_authenticate(user=self.test_user)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("username", response.data)
        self.assertIn("email", response.data)
        self.assertIn("id", response.data)

    def test_current_user_unauthenticated_returns_null(self):
        """Test that current user endpoint returns null for unauthenticated user."""
        url = f"{BASE_URL}/current-user/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)

    def test_delete_account_success_returns_200(self):
        """Test that successful account deletion returns 200 status code."""
        url = f"{BASE_URL}/delete-account/"
        # Create a user specifically for deletion
        user_to_delete = self.test_user
        self.client.force_authenticate(user=user_to_delete)
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        # Verify user was deleted (already deleted by the endpoint)
        self.assertFalse(User.objects.filter(username=user_to_delete.username).exists())
        # Note: user_to_delete is already deleted by the endpoint, no cleanup needed

    def test_login_invalid_credentials_returns_401(self):
        """Test that login with invalid credentials returns 401."""
        url = f"{BASE_URL}/login/"
        data = {"username": "MircelGagiul359", "password": "wrongpassword"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_signup_password_mismatch_returns_400(self):
        """Test that signup with mismatched passwords returns 400."""
        url = f"{BASE_URL}/signup/"
        data = {
            "username": "MircelGagiul359Mismatch",
            "email": "MircelRekinuMismatch@yahoo.com",
            "password1": "testpass123femei",
            "password2": "differentpass",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_unauthenticated_returns_401(self):
        """Test that logout without authentication returns 401."""
        url = f"{BASE_URL}/logout/"
        response = self.client.post(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_account_unauthenticated_returns_401(self):
        """Test that delete account without authentication returns 401."""
        url = f"{BASE_URL}/delete-account/"
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_reset_confirm_success(self):
        uid = urlsafe_base64_encode(force_bytes(self.test_user.pk))
        token = default_token_generator.make_token(self.test_user)
        url = f"{BASE_URL}/password-reset/confirm/"
        data = {
            "uid": uid,
            "token": token,
            "new_password1": "newpass123femei",
            "new_password2": "newpass123femei",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.check_password("newpass123femei"))

    def test_password_reset_confirm_invalid_token_returns_400(self):
        uid = urlsafe_base64_encode(force_bytes(self.test_user.pk))
        url = f"{BASE_URL}/password-reset/confirm/"
        data = {
            "uid": uid,
            "token": "invalid-token",
            "new_password1": "newpass123femei",
            "new_password2": "newpass123femei",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_success_returns_200(self):
        url = f"{BASE_URL}/change-password/"
        self.client.force_authenticate(user=self.test_user)
        data = {
            "current_password": "testpass123femei",
            "new_password1": "newpass456femei",
            "new_password2": "newpass456femei",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.check_password("newpass456femei"))

    def test_update_username_success_returns_200(self):
        url = f"{BASE_URL}/update-username/"
        self.client.force_authenticate(user=self.test_user)
        response = self.client.patch(url, {"username": "MircelGagiul361"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "MircelGagiul361")
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.username, "MircelGagiul361")

    def test_update_preferences_success_returns_200(self):
        url = f"{BASE_URL}/preferences/"
        self.client.force_authenticate(user=self.test_user)
        response = self.client.patch(url, {"preferred_unit": "LBS"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["preferred_unit"], "LBS")
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.preferred_unit, "LBS")


class JWTTokenAPITestCase(TestCase):
    """Tests for the simplejwt token endpoints used by the frontend login flow."""

    def setUp(self):
        self.client = APIClient()
        self.test_user = create_test_user("MircelTokenist", "testpass123femei")

    def test_token_obtain_returns_access_and_refresh(self):
        response = self.client.post(
            "/api/token/",
            {"username": "MircelTokenist", "password": "testpass123femei"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_refresh_returns_new_access(self):
        tokens = self.client.post(
            "/api/token/",
            {"username": "MircelTokenist", "password": "testpass123femei"},
            format="json",
        ).data
        response = self.client.post("/api/token/refresh/", {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
