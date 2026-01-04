"""
User models for authentication.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """Custom manager for CustomUser that uses email instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Uses email as the primary login identifier instead of username.
    """
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False, help_text='Whether the user has verified their email.')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class TokenBlacklist(models.Model):
    """
    Model to store blacklisted refresh tokens.
    Used for logout functionality to prevent token reuse.
    """
    refresh_token = models.TextField()
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text='When the token will naturally expire.')

    class Meta:
        verbose_name = 'Blacklisted Token'
        verbose_name_plural = 'Blacklisted Tokens'
        ordering = ['-blacklisted_at']
        indexes = [
            models.Index(fields=['refresh_token']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f'Blacklisted token: {self.refresh_token[:20]}...'

    def is_expired(self):
        """Check if the token has expired."""
        return timezone.now() > self.expires_at
