"""
Serializers for user authentication.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from users.utils import verify_otp, store_otp, generate_otp, send_otp_email

CustomUser = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile information."""

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'is_verified', 'created_at', 'is_staff')
        read_only_fields = ('id', 'created_at')


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration (step 1: enter email)."""
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'password')

    def validate_password(self, value):
        """Validate password strength."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate_email(self, value):
        """Validate email uniqueness."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        """Create user and send OTP."""
        email = validated_data['email']
        password = validated_data['password']

        # Create user with temporary password
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            is_verified=False
        )

        # Generate and send OTP
        otp = generate_otp(6)
        store_otp(email, otp, ttl=300)  # 5 minutes
        send_otp_email(email, otp)

        return user


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification (step 2: verify email with OTP)."""
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(max_length=10, required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate_password(self, value):
        """Validate password strength."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, data):
        """Verify OTP and user existence."""
        email = data.get('email')
        otp = data.get('otp')

        # Check if user exists
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist.')

        # Verify OTP
        is_valid, message = verify_otp(email, otp)
        if not is_valid:
            raise serializers.ValidationError({'otp': message})

        data['user'] = user
        return data

    def create(self, validated_data):
        """Set password and mark user as verified."""
        user = validated_data['user']
        password = validated_data['password']

        # Update user
        user.set_password(password)
        user.is_verified = True
        user.save()

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

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password.')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid email or password.')

        if not user.is_active:
            raise serializers.ValidationError('This user account is inactive.')

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
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        """Validate new password strength."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
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
