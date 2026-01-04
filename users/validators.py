"""
Custom validators for user authentication.
"""
import re
from django.core.exceptions import ValidationError


class ComplexPasswordValidator:
    """
    Validate that password contains:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character (!@#$%^&*)
    """

    def validate(self, password, user=None):
        """Validate password complexity."""
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')

        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')

        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')

        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one digit.')

        if not re.search(r'[!@#$%^&*]', password):
            raise ValidationError('Password must contain at least one special character (!@#$%^&*).')

    def get_help_text(self):
        """Return help text for password requirements."""
        return (
            'Password must contain at least 8 characters with uppercase, '
            'lowercase, digit, and special character (!@#$%^&*) each.'
        )
