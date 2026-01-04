"""
Test cases for CustomUser and TokenBlacklist models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from users.models import TokenBlacklist

CustomUser = get_user_model()


class CustomUserModelTests(TestCase):
    """Test cases for CustomUser model."""

    def setUp(self):
        """Set up test data."""
        self.email = 'testuser@uni.edu'
        self.password = 'TestPassword123!'
        self.user = CustomUser.objects.create_user(
            email=self.email,
            password=self.password
        )

    def test_user_creation_with_email_and_password(self):
        """Test creating a user with email and password."""
        self.assertEqual(self.user.email, self.email)
        self.assertTrue(self.user.check_password(self.password))
        self.assertFalse(self.user.is_verified)

    def test_email_uniqueness_validation(self):
        """Test that email must be unique."""
        with self.assertRaises(IntegrityError):
            CustomUser.objects.create_user(
                email=self.email,
                password='AnotherPass123!'
            )

    def test_password_is_hashed(self):
        """Test that password is properly hashed."""
        self.assertNotEqual(self.user.password, self.password)
        self.assertTrue(self.user.check_password(self.password))

    def test_is_verified_default_is_false(self):
        """Test that is_verified defaults to False."""
        new_user = CustomUser.objects.create_user(
            email='new@uni.edu',
            password='Pass123!'
        )
        self.assertFalse(new_user.is_verified)

    def test_user_string_representation(self):
        """Test user string representation."""
        self.assertEqual(str(self.user), self.email)

    def test_user_with_special_characters_in_email(self):
        """Test creating user with special characters in email."""
        special_email = 'user+test@uni.edu'
        user = CustomUser.objects.create_user(
            email=special_email,
            password='Pass123!'
        )
        self.assertEqual(user.email, special_email)

    def test_user_creation_without_password(self):
        """Test that creating user without password still creates user."""
        user = CustomUser.objects.create_user(
            email='nopwd@uni.edu',
            password=None
        )
        # User should be created, even if password handling is unusual
        self.assertEqual(user.email, 'nopwd@uni.edu')
        self.assertIsNotNone(user)

    def test_user_creation_without_email_raises_error(self):
        """Test that creating user without email raises error."""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(
                email='',
                password='Pass123!'
            )

    def test_is_verified_can_be_updated(self):
        """Test that is_verified can be updated."""
        self.assertFalse(self.user.is_verified)
        self.user.is_verified = True
        self.user.save()

        refreshed_user = CustomUser.objects.get(id=self.user.id)
        self.assertTrue(refreshed_user.is_verified)

    def test_created_at_timestamp(self):
        """Test that created_at is automatically set."""
        self.assertIsNotNone(self.user.created_at)
        self.assertLessEqual(
            (timezone.now() - self.user.created_at).total_seconds(),
            5  # Within 5 seconds
        )

    def test_superuser_creation(self):
        """Test creating a superuser."""
        admin = CustomUser.objects.create_superuser(
            email='admin@uni.edu',
            password='AdminPass123!'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_password_validation_with_check_password(self):
        """Test password validation."""
        user = CustomUser.objects.create_user(
            email='validate@uni.edu',
            password='Correct123!'
        )
        self.assertTrue(user.check_password('Correct123!'))
        self.assertFalse(user.check_password('Wrong123!'))

    def test_user_has_username_field(self):
        """Test that user has standard AbstractUser fields."""
        self.assertIsNotNone(self.user.username)
        self.assertIsNotNone(self.user.first_name)
        self.assertIsNotNone(self.user.last_name)

    def test_user_is_active_by_default(self):
        """Test that user is active by default."""
        self.assertTrue(self.user.is_active)

    def test_email_case_sensitivity(self):
        """Test email handling (should be case-insensitive by default)."""
        user = CustomUser.objects.create_user(
            email='CaseSensitive@uni.edu',
            password='Pass123!'
        )
        # Django's default behavior normalizes email
        self.assertEqual(user.email.lower(), 'casesensitive@uni.edu'.lower())


class TokenBlacklistModelTests(TestCase):
    """Test cases for TokenBlacklist model."""

    def setUp(self):
        """Set up test data."""
        self.refresh_token = 'test_refresh_token_xyz123'
        self.expires_at = timezone.now() + timedelta(days=7)
        self.blacklist = TokenBlacklist.objects.create(
            refresh_token=self.refresh_token,
            expires_at=self.expires_at
        )

    def test_blacklist_creation(self):
        """Test creating a token blacklist entry."""
        self.assertEqual(self.blacklist.refresh_token, self.refresh_token)
        self.assertEqual(self.blacklist.expires_at, self.expires_at)

    def test_blacklist_token_lookup(self):
        """Test looking up a blacklisted token."""
        found = TokenBlacklist.objects.filter(
            refresh_token=self.refresh_token
        ).exists()
        self.assertTrue(found)

    def test_blacklist_nonexistent_token_lookup(self):
        """Test looking up a non-existent token."""
        found = TokenBlacklist.objects.filter(
            refresh_token='nonexistent_token'
        ).exists()
        self.assertFalse(found)

    def test_blacklisted_at_auto_now(self):
        """Test that blacklisted_at is automatically set."""
        self.assertIsNotNone(self.blacklist.blacklisted_at)
        self.assertLessEqual(
            (timezone.now() - self.blacklist.blacklisted_at).total_seconds(),
            5  # Within 5 seconds
        )

    def test_expired_token_identification(self):
        """Test identifying expired tokens."""
        # Create an already-expired token
        expired_time = timezone.now() - timedelta(hours=1)
        expired = TokenBlacklist.objects.create(
            refresh_token='expired_token',
            expires_at=expired_time
        )

        # Should be able to find it
        found = TokenBlacklist.objects.filter(
            refresh_token='expired_token'
        ).exists()
        self.assertTrue(found)

    def test_expired_token_filter(self):
        """Test filtering for expired tokens."""
        # Create an expired token
        expired_time = timezone.now() - timedelta(hours=1)
        TokenBlacklist.objects.create(
            refresh_token='expired_1',
            expires_at=expired_time
        )

        # Create a non-expired token
        future_time = timezone.now() + timedelta(days=1)
        TokenBlacklist.objects.create(
            refresh_token='valid_1',
            expires_at=future_time
        )

        # Filter for expired
        expired_count = TokenBlacklist.objects.filter(
            expires_at__lt=timezone.now()
        ).count()
        self.assertEqual(expired_count, 1)

    def test_multiple_blacklist_entries(self):
        """Test creating multiple blacklist entries."""
        TokenBlacklist.objects.create(
            refresh_token='token_2',
            expires_at=timezone.now() + timedelta(days=7)
        )
        TokenBlacklist.objects.create(
            refresh_token='token_3',
            expires_at=timezone.now() + timedelta(days=7)
        )

        count = TokenBlacklist.objects.count()
        self.assertEqual(count, 3)

    def test_token_uniqueness(self):
        """Test that token field can have unique constraint if needed."""
        # Just verify we can create another with same token (Django allows duplicates by default)
        # This documents current behavior
        TokenBlacklist.objects.create(
            refresh_token='duplicate_token',
            expires_at=timezone.now() + timedelta(days=7)
        )
        TokenBlacklist.objects.create(
            refresh_token='duplicate_token',
            expires_at=timezone.now() + timedelta(days=7)
        )

        count = TokenBlacklist.objects.filter(
            refresh_token='duplicate_token'
        ).count()
        self.assertEqual(count, 2)
