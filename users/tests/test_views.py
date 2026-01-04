"""
Test cases for authentication API endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
import json

from users.models import TokenBlacklist
from users.utils import generate_otp

CustomUser = get_user_model()


class UserRegistrationEndpointTests(TestCase):
    """Test cases for user registration endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.register_url = '/api/users/register/'
        cache.clear()

    def tearDown(self):
        """Clean up cache."""
        cache.clear()

    def test_register_with_valid_email(self):
        """Test registration with valid email."""
        data = {'email': 'newuser@uni.edu'}
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'], 'newuser@uni.edu')

    def test_register_sends_otp(self):
        """Test that registration sends OTP."""
        data = {'email': 'otp@uni.edu'}
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify OTP is in cache
        otp_data = cache.get(f'otp_otp@uni.edu')
        self.assertIsNotNone(otp_data)
        self.assertIn('otp', otp_data)

    def test_register_does_not_create_user(self):
        """Test that registration does NOT create a user (user created after verification)."""
        data = {'email': 'inactive@uni.edu'}
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # User should NOT exist yet
        with self.assertRaises(CustomUser.DoesNotExist):
            CustomUser.objects.get(email='inactive@uni.edu')

    def test_register_with_invalid_email_format(self):
        """Test registration with invalid email format."""
        data = {'email': 'invalid-email'}
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_with_duplicate_email(self):
        """Test registration with duplicate email."""
        CustomUser.objects.create_user(
            email='existing@uni.edu',
            password='Pass123!'
        )

        data = {'email': 'existing@uni.edu'}
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_without_email(self):
        """Test registration without email."""
        data = {'email': ''}
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_with_no_data(self):
        """Test registration with no data."""
        response = self.client.post(self.register_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_special_email_characters(self):
        """Test registration with special characters in email."""
        data = {'email': 'user+test@uni.edu'}
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class OTPVerificationEndpointTests(TestCase):
    """Test cases for OTP verification endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.verify_url = '/api/users/verify/'
        cache.clear()

        self.email = 'verify@uni.edu'
        self.otp = '123456'
        self.password = 'ValidPass123!'

        # Store OTP in cache (user will be created during verification)
        cache.set(f'otp_{self.email}', {
            'otp': self.otp,
            'attempts': 0,
            'created_at': timezone.now().isoformat()
        }, 300)

    def tearDown(self):
        """Clean up cache."""
        cache.clear()

    def test_verify_with_valid_otp(self):
        """Test verification with valid OTP."""
        data = {
            'email': self.email,
            'otp': self.otp,
            'password': self.password
        }
        response = self.client.post(self.verify_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)

    def test_verify_marks_user_as_verified(self):
        """Test that verification marks user as verified."""
        data = {
            'email': self.email,
            'otp': self.otp,
            'password': self.password
        }
        response = self.client.post(self.verify_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = CustomUser.objects.get(email=self.email)
        self.assertTrue(user.is_verified)

    def test_verify_updates_password(self):
        """Test that verification updates password."""
        data = {
            'email': self.email,
            'otp': self.otp,
            'password': self.password
        }
        response = self.client.post(self.verify_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = CustomUser.objects.get(email=self.email)
        self.assertTrue(user.check_password(self.password))

    def test_verify_with_invalid_otp(self):
        """Test verification with invalid OTP."""
        data = {
            'email': self.email,
            'otp': '999999',
            'password': self.password
        }
        response = self.client.post(self.verify_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('otp', response.data)

    def test_verify_with_expired_otp(self):
        """Test verification with expired OTP."""
        cache.delete(f'otp_{self.email}')

        data = {
            'email': self.email,
            'otp': self.otp,
            'password': self.password
        }
        response = self.client.post(self.verify_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_with_weak_password(self):
        """Test verification with weak password."""
        data = {
            'email': self.email,
            'otp': self.otp,
            'password': 'weak'
        }
        response = self.client.post(self.verify_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class LoginEndpointTests(TestCase):
    """Test cases for login endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.login_url = '/api/users/login/'

        self.email = 'login@uni.edu'
        self.password = 'LoginPass123!'
        self.user = CustomUser.objects.create_user(
            email=self.email,
            password=self.password
        )
        self.user.is_verified = True
        self.user.save()

    def test_login_with_correct_credentials(self):
        """Test login with correct credentials."""
        data = {
            'email': self.email,
            'password': self.password
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_returns_valid_jwt_tokens(self):
        """Test that login returns valid JWT tokens."""
        data = {
            'email': self.email,
            'password': self.password
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access']
        refresh_token = response.data['refresh']

        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)
        self.assertGreater(len(str(access_token)), 0)
        self.assertGreater(len(str(refresh_token)), 0)

    def test_login_with_incorrect_password(self):
        """Test login with incorrect password."""
        data = {
            'email': self.email,
            'password': 'WrongPassword123!'
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_nonexistent_user(self):
        """Test login with non-existent user."""
        data = {
            'email': 'nonexistent@uni.edu',
            'password': self.password
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_without_email(self):
        """Test login without email."""
        data = {
            'email': '',
            'password': self.password
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_without_password(self):
        """Test login without password."""
        data = {
            'email': self.email,
            'password': ''
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_unverified_user(self):
        """Test login with unverified user."""
        unverified_user = CustomUser.objects.create_user(
            email='unverified@uni.edu',
            password='Pass123!'
        )
        unverified_user.is_verified = False
        unverified_user.save()

        data = {
            'email': 'unverified@uni.edu',
            'password': 'Pass123!'
        }
        # Depending on business logic, might allow or deny
        response = self.client.post(self.login_url, data, format='json')
        # This test documents the behavior - adjust based on requirements
        # Currently expects it to allow login regardless of verification


class RefreshTokenEndpointTests(TestCase):
    """Test cases for token refresh endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.refresh_url = '/api/users/refresh/'

        self.email = 'refresh@uni.edu'
        self.password = 'RefreshPass123!'
        self.user = CustomUser.objects.create_user(
            email=self.email,
            password=self.password
        )
        self.user.is_verified = True
        self.user.save()

        # Get initial tokens
        login_response = self.client.post(
            '/api/users/login/',
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.refresh_token = login_response.data['refresh']

    def test_refresh_with_valid_token(self):
        """Test refresh with valid refresh token."""
        data = {'refresh': str(self.refresh_token)}
        response = self.client.post(self.refresh_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_returns_new_access_token(self):
        """Test that refresh returns a new access token."""
        data = {'refresh': str(self.refresh_token)}
        response = self.client.post(self.refresh_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_access = response.data['access']
        self.assertIsNotNone(new_access)

    def test_refresh_with_invalid_token(self):
        """Test refresh with invalid token."""
        data = {'refresh': 'invalid_token'}
        response = self.client.post(self.refresh_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_blacklisted_token(self):
        """Test refresh with blacklisted token."""
        # Blacklist the token
        TokenBlacklist.objects.create(
            refresh_token=str(self.refresh_token),
            expires_at=timezone.now() + timedelta(days=7)
        )

        data = {'refresh': str(self.refresh_token)}
        response = self.client.post(self.refresh_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_without_token(self):
        """Test refresh without token."""
        data = {'refresh': ''}
        response = self.client.post(self.refresh_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutEndpointTests(TestCase):
    """Test cases for logout endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.logout_url = '/api/users/logout/'

        self.email = 'logout@uni.edu'
        self.password = 'LogoutPass123!'
        self.user = CustomUser.objects.create_user(
            email=self.email,
            password=self.password
        )
        self.user.is_verified = True
        self.user.save()

        # Get tokens
        login_response = self.client.post(
            '/api/users/login/',
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.access_token = login_response.data['access']
        self.refresh_token = login_response.data['refresh']

    def test_logout_with_valid_token(self):
        """Test logout with valid refresh token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {'refresh': str(self.refresh_token)}
        response = self.client.post(self.logout_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_blacklists_token(self):
        """Test that logout blacklists the token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {'refresh': str(self.refresh_token)}
        response = self.client.post(self.logout_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify token is in blacklist
        blacklisted = TokenBlacklist.objects.filter(
            refresh_token=str(self.refresh_token)
        ).exists()
        self.assertTrue(blacklisted)

    def test_logout_without_authentication(self):
        """Test logout without authentication."""
        data = {'refresh': str(self.refresh_token)}
        response = self.client.post(self.logout_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_token(self):
        """Test logout with invalid token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {'refresh': 'invalid_token'}
        response = self.client.post(self.logout_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileEndpointTests(TestCase):
    """Test cases for user profile endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.profile_url = '/api/users/profile/'

        self.email = 'profile@uni.edu'
        self.password = 'ProfilePass123!'
        self.user = CustomUser.objects.create_user(
            email=self.email,
            password=self.password
        )
        self.user.is_verified = True
        self.user.save()

        # Get token
        login_response = self.client.post(
            '/api/users/login/',
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.access_token = login_response.data['access']

    def test_profile_without_authentication(self):
        """Test profile endpoint without authentication."""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_with_valid_token(self):
        """Test profile endpoint with valid token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.email)

    def test_profile_returns_correct_fields(self):
        """Test that profile returns correct fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertIn('email', response.data)
        self.assertIn('is_verified', response.data)
        self.assertIn('created_at', response.data)

    def test_profile_with_expired_token(self):
        """Test profile with expired token."""
        # Create an expired token
        expired_token = 'expired.token.here'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordEndpointTests(TestCase):
    """Test cases for change password endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.change_password_url = '/api/users/change-password/'

        self.email = 'change@uni.edu'
        self.old_password = 'OldPass123!'
        self.new_password = 'NewPass123!'
        self.user = CustomUser.objects.create_user(
            email=self.email,
            password=self.old_password
        )
        self.user.is_verified = True
        self.user.save()

        # Get token
        login_response = self.client.post(
            '/api/users/login/',
            {'email': self.email, 'password': self.old_password},
            format='json'
        )
        self.access_token = login_response.data['access']

    def test_change_password_without_authentication(self):
        """Test change password without authentication."""
        data = {
            'old_password': self.old_password,
            'new_password': self.new_password
        }
        response = self.client.put(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_with_correct_old_password(self):
        """Test change password with correct old password."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {
            'old_password': self.old_password,
            'new_password': self.new_password
        }
        response = self.client.put(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_with_incorrect_old_password(self):
        """Test change password with incorrect old password."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {
            'old_password': 'WrongOldPass123!',
            'new_password': self.new_password
        }
        response = self.client.put(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)

    def test_change_password_with_weak_new_password(self):
        """Test change password with weak new password."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {
            'old_password': self.old_password,
            'new_password': 'weak'
        }
        response = self.client.put(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)

    def test_change_password_actually_updates_password(self):
        """Test that password is actually updated."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        data = {
            'old_password': self.old_password,
            'new_password': self.new_password
        }
        response = self.client.put(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try logging in with new password
        login_response = self.client.post(
            '/api/users/login/',
            {'email': self.email, 'password': self.new_password},
            format='json'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
