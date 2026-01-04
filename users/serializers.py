"""
Serializers for user authentication.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from users.utils import verify_otp, store_otp, generate_otp, send_otp_email
from users.validators import ComplexPasswordValidator

CustomUser = get_user_model()
password_validator = ComplexPasswordValidator()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile information."""

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'is_verified', 'created_at', 'is_staff')
        read_only_fields = ('id', 'created_at')


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration (step 1: enter email only)."""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Validate email uniqueness."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        """Send OTP to email (user will be created after verification)."""
        email = validated_data['email']

        # Generate and send OTP
        otp = generate_otp(6)
        store_otp(email, otp, ttl=300)  # 5 minutes
        send_otp_email(email, otp)

        # Return email only (user will be created during verification)
        return {'email': email}


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification (step 2: verify email with OTP and set password)."""
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(max_length=10, required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate_password(self, value):
        """Validate password complexity."""
        try:
            password_validator.validate(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message if hasattr(e, 'message') else str(e.messages[0]) if e.messages else 'Invalid password')
        return value

    def validate(self, data):
        """Verify OTP."""
        email = data.get('email')
        otp = data.get('otp')

        # Verify OTP
        is_valid, message = verify_otp(email, otp)
        if not is_valid:
            raise serializers.ValidationError({'otp': message})

        # Store email for create() method (user will be created now)
        data['email'] = email
        return data

    def create(self, validated_data):
        """Create user with verified email and password."""
        email = validated_data['email']
        password = validated_data['password']

        # Create user (first time, after OTP verification)
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            is_verified=True
        )

        return user

    def to_representation(self, instance):
        """Return user data in response."""
        user_serializer = UserSerializer(instance)
        return {'user': user_serializer.data}


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """Verify email and password."""
        email = data.get('email')
        password = data.get('password')

        # Check if fields are provided
        if not email:
            raise serializers.ValidationError({'email': 'Email is required.'})
        if not password:
            raise serializers.ValidationError({'password': 'Password is required.'})

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(
                {'non_field_errors': ['Invalid email or password.']}
            )

        if not user.check_password(password):
            raise serializers.ValidationError(
                {'non_field_errors': ['Invalid email or password.']}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {'non_field_errors': ['This user account is inactive.']}
            )

        data['user'] = user
        return data

    def create(self, validated_data):
        """Generate JWT tokens."""
        user = validated_data['user']
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def to_representation(self, instance):
        """Return tokens in response."""
        return instance


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for token refresh."""
    refresh = serializers.CharField(required=True)

    def validate_refresh(self, value):
        """Validate refresh token format."""
        # The actual validation happens in the view with SimpleJWT
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate_new_password(self, value):
        """Validate new password strength."""
        try:
            password_validator.validate(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message if hasattr(e, 'message') else str(e.messages[0]) if e.messages else 'Invalid password')
        return value

    def validate(self, data):
        """Verify old password."""
        user = self.context['request'].user
        old_password = data.get('old_password')

        if not user.check_password(old_password):
            raise serializers.ValidationError({'old_password': 'Old password is incorrect.'})

        return data

    def create(self, validated_data):
        """Update password."""
        user = self.context['request'].user
        user.set_password(validated_data['new_password'])
        user.save()
        return user

    def to_representation(self, instance):
        """Return success message."""
        return {'message': 'Password changed successfully.'}


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout (blacklist refresh token)."""
    refresh = serializers.CharField(required=True)

    def validate_refresh(self, value):
        """Validate refresh token format."""
        return value

    def to_representation(self, instance):
        """Return success message."""
        return {'message': 'Logged out successfully.'}
