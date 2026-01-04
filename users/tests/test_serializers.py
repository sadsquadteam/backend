"""
Test cases for authentication serializers.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.exceptions import ValidationError
from django.utils import timezone
import json

from users.serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    OTPVerificationSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
)
from users.utils import generate_otp

CustomUser = get_user_model()


class UserSerializerTests(TestCase):
    """Test cases for UserSerializer."""

    def setUp(self):
        """Set up test data."""
        self.user = CustomUser.objects.create_user(
            email='test@uni.edu',
            password='Pass123!'
        )
        self.user.is_verified = True
        self.user.save()

    def test_user_serializer_contains_correct_fields(self):
        """Test that serializer returns correct fields."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertIn('id', data)
        self.assertIn('email', data)
        self.assertIn('is_verified', data)
        self.assertIn('created_at', data)
        self.assertIn('is_staff', data)

    def test_user_serializer_data_values(self):
        """Test that serializer returns correct values."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data['email'], 'test@uni.edu')
        self.assertTrue(data['is_verified'])
        self.assertFalse(data['is_staff'])

    def test_user_serializer_password_not_included(self):
        """Test that password is not included in serializer output."""
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertNotIn('password', data)


class UserRegistrationSerializerTests(TestCase):
    """Test cases for UserRegistrationSerializer."""

    def test_registration_with_valid_email_and_password(self):
        """Test registration with valid email and password."""
        data = {
            'email': 'newuser@uni.edu',
            'password': 'ValidPass123!'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_registration_with_invalid_email_format(self):
        """Test registration with invalid email format."""
        data = {
            'email': 'invalid-email',
            'password': 'ValidPass123!'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_registration_with_weak_password_short(self):
        """Test registration with weak password (too short)."""
        data = {
            'email': 'user@uni.edu',
            'password': 'Short1!'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_registration_with_no_uppercase_password(self):
        """Test registration with password missing uppercase."""
        data = {
            'email': 'user@uni.edu',
            'password': 'lowercase123!'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_registration_with_no_lowercase_password(self):
        """Test registration with password missing lowercase."""
        data = {
            'email': 'user@uni.edu',
            'password': 'UPPERCASE123!'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_registration_with_no_digit_password(self):
        """Test registration with password missing digit."""
        data = {
            'email': 'user@uni.edu',
            'password': 'NoDigitsHere!'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_registration_with_no_special_char_password(self):
        """Test registration with password missing special character."""
        data = {
            'email': 'user@uni.edu',
            'password': 'NoSpecialChar123'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_registration_with_duplicate_email(self):
        """Test registration with duplicate email."""
        CustomUser.objects.create_user(
            email='existing@uni.edu',
            password='Pass123!'
        )

        data = {
            'email': 'existing@uni.edu',
            'password': 'NewPass123!'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_registration_creates_user_with_is_verified_false(self):
        """Test that registration creates user with is_verified=False."""
        data = {
            'email': 'newuser@uni.edu',
            'password': 'ValidPass123!'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertFalse(user.is_verified)
        self.assertEqual(user.email, 'newuser@uni.edu')

    def test_registration_without_email(self):
        """Test registration without email."""
        data = {
            'email': '',
            'password': 'ValidPass123!'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_registration_without_password(self):
        """Test registration without password."""
        data = {
            'email': 'user@uni.edu',
            'password': ''
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class OTPVerificationSerializerTests(TestCase):
    """Test cases for OTPVerificationSerializer."""

    def setUp(self):
        """Set up test data."""
        cache.clear()
        self.email = 'verify@uni.edu'
        self.otp = '123456'
        self.password = 'ValidPass123!'

        # Create user and store OTP in cache
        self.user = CustomUser.objects.create_user(
            email=self.email,
            password='temp_password'
        )
        cache.set(f'otp_{self.email}', {
            'otp': self.otp,
            'attempts': 0,
            'created_at': timezone.now().isoformat()
        }, 300)  # 5 minutes

    def tearDown(self):
        """Clean up cache."""
        cache.clear()

    def test_verification_with_valid_otp(self):
        """Test verification with valid OTP."""
        data = {
            'email': self.email,
            'otp': self.otp,
            'password': self.password
        }
        serializer = OTPVerificationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_verification_with_invalid_otp(self):
        """Test verification with invalid OTP."""
        data = {
            'email': self.email,
            'otp': '999999',
            'password': self.password
        }
        serializer = OTPVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('otp', serializer.errors)

    def test_verification_with_expired_otp(self):
        """Test verification with expired OTP."""
        # Clear cache to simulate expired OTP
        cache.delete(f'otp_{self.email}')

        data = {
            'email': self.email,
            'otp': self.otp,
            'password': self.password
        }
        serializer = OTPVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_verification_with_nonexistent_user(self):
        """Test verification with non-existent user."""
        data = {
            'email': 'nonexistent@uni.edu',
            'otp': self.otp,
            'password': self.password
        }
        serializer = OTPVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_verification_sets_is_verified_true(self):
        """Test that verification sets is_verified=True."""
        data = {
            'email': self.email,
            'otp': self.otp,
            'password': self.password
        }
        serializer = OTPVerificationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertTrue(user.is_verified)

    def test_verification_updates_password(self):
        """Test that verification updates password."""
        new_password = 'NewValidPass123!'
        data = {
            'email': self.email,
            'otp': self.otp,
            'password': new_password
        }
        serializer = OTPVerificationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertTrue(user.check_password(new_password))

    def test_verification_with_weak_password(self):
        """Test verification with weak password."""
        data = {
            'email': self.email,
            'otp': self.otp,
            'password': 'weak'
        }
        serializer = OTPVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class LoginSerializerTests(TestCase):
    """Test cases for LoginSerializer."""

    def setUp(self):
        """Set up test data."""
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
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_login_returns_tokens(self):
        """Test that login returns access and refresh tokens."""
        data = {
            'email': self.email,
            'password': self.password
        }
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        result = serializer.validated_data
        self.assertIn('access', result)
        self.assertIn('refresh', result)

    def test_login_with_incorrect_password(self):
        """Test login with incorrect password."""
        data = {
            'email': self.email,
            'password': 'WrongPassword123!'
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_login_with_nonexistent_user(self):
        """Test login with non-existent user."""
        data = {
            'email': 'nonexistent@uni.edu',
            'password': self.password
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_login_without_email(self):
        """Test login without email."""
        data = {
            'email': '',
            'password': self.password
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_login_without_password(self):
        """Test login without password."""
        data = {
            'email': self.email,
            'password': ''
        }
        serializer = LoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_login_tokens_are_valid_jwt(self):
        """Test that returned tokens are valid JWT."""
        data = {
            'email': self.email,
            'password': self.password
        }
        serializer = LoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        result = serializer.validated_data
        access_token = result['access']
        refresh_token = result['refresh']

        # Verify they are not empty strings
        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)
        self.assertGreater(len(str(access_token)), 0)
        self.assertGreater(len(str(refresh_token)), 0)


class ChangePasswordSerializerTests(TestCase):
    """Test cases for ChangePasswordSerializer."""

    def setUp(self):
        """Set up test data."""
        self.email = 'change@uni.edu'
        self.old_password = 'OldPass123!'
        self.new_password = 'NewPass123!'
        self.user = CustomUser.objects.create_user(
            email=self.email,
            password=self.old_password
        )

    def test_change_password_with_correct_old_password(self):
        """Test changing password with correct old password."""
        data = {
            'old_password': self.old_password,
            'new_password': self.new_password
        }
        serializer = ChangePasswordSerializer(
            self.user,
            data=data
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_change_password_with_incorrect_old_password(self):
        """Test changing password with incorrect old password."""
        data = {
            'old_password': 'WrongOldPass123!',
            'new_password': self.new_password
        }
        serializer = ChangePasswordSerializer(
            self.user,
            data=data
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)

    def test_change_password_with_weak_new_password(self):
        """Test changing password with weak new password."""
        data = {
            'old_password': self.old_password,
            'new_password': 'weak'
        }
        serializer = ChangePasswordSerializer(
            self.user,
            data=data
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)

    def test_change_password_updates_user_password(self):
        """Test that password is actually updated."""
        data = {
            'old_password': self.old_password,
            'new_password': self.new_password
        }
        serializer = ChangePasswordSerializer(
            self.user,
            data=data
        )
        self.assertTrue(serializer.is_valid())

        updated_user = serializer.save()
        self.assertTrue(updated_user.check_password(self.new_password))
        self.assertFalse(updated_user.check_password(self.old_password))

    def test_change_password_without_old_password(self):
        """Test changing password without old password."""
        data = {
            'old_password': '',
            'new_password': self.new_password
        }
        serializer = ChangePasswordSerializer(
            self.user,
            data=data
        )
        self.assertFalse(serializer.is_valid())

    def test_change_password_without_new_password(self):
        """Test changing password without new password."""
        data = {
            'old_password': self.old_password,
            'new_password': ''
        }
        serializer = ChangePasswordSerializer(
            self.user,
            data=data
        )
        self.assertFalse(serializer.is_valid())
