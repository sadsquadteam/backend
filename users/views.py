"""
API views for user authentication.
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from datetime import datetime as dt

from users.models import TokenBlacklist
from users.serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    OTPVerificationSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    LogoutSerializer,
)
from users.utils import verify_otp, store_otp, generate_otp, send_otp_email

CustomUser = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user and send OTP to email.

    POST /api/users/register/
    Body: { "email": "user@uni.edu" }
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                'message': 'OTP sent to email. Please verify your email.',
                'email': user.email
            },
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify email with OTP and set password.

    POST /api/users/verify/
    Body: { "email": "user@uni.edu", "otp": "123456", "password": "SecurePass123!" }
    """
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                'message': 'Email verified successfully. You can now login.',
                'user': UserSerializer(user).data
            },
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return JWT tokens.

    POST /api/users/login/
    Body: { "email": "user@uni.edu", "password": "SecurePass123!" }
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        tokens = serializer.save()
        return Response(tokens, status=status.HTTP_200_OK)

    # Distinguish between validation errors (400) and auth errors (401)
    errors = serializer.errors

    # If it's a missing/invalid field error, return 400
    if any(key in errors for key in ['email', 'password']):
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    # Otherwise it's an authentication error, return 401
    return Response(
        errors or {'non_field_errors': ['Invalid email or password.']},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh access token using refresh token.

    POST /api/users/refresh/
    Body: { "refresh": "refresh_token_here" }
    """
    refresh_token_str = request.data.get('refresh')

    if not refresh_token_str:
        return Response(
            {'refresh': ['This field is required.']},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if token is blacklisted
    is_blacklisted = TokenBlacklist.objects.filter(
        refresh_token=refresh_token_str
    ).exists()

    if is_blacklisted:
        return Response(
            {'detail': 'Token is blacklisted.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        refresh = RefreshToken(refresh_token_str)
        return Response(
            {'access': str(refresh.access_token)},
            status=status.HTTP_200_OK
        )
    except (InvalidToken, TokenError):
        return Response(
            {'detail': 'Invalid or expired refresh token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting refresh token.

    POST /api/users/logout/
    Body: { "refresh": "refresh_token_here" }
    Headers: Authorization: Bearer <access_token>
    """
    refresh_token_str = request.data.get('refresh')

    if not refresh_token_str:
        return Response(
            {'refresh': ['This field is required.']},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        refresh = RefreshToken(refresh_token_str)
        # Get expiry time from token
        expires_at = dt.fromtimestamp(
            refresh['exp'],
            tz=timezone.UTC
        )

        # Add to blacklist
        TokenBlacklist.objects.create(
            refresh_token=refresh_token_str,
            expires_at=expires_at
        )

        return Response(
            {'message': 'Logged out successfully.'},
            status=status.HTTP_200_OK
        )
    except (InvalidToken, TokenError):
        return Response(
            {'detail': 'Invalid refresh token.'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Get current user profile.

    GET /api/users/profile/
    Headers: Authorization: Bearer <access_token>
    """
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password.

    PUT /api/users/change-password/
    Body: { "old_password": "OldPass123!", "new_password": "NewPass123!" }
    Headers: Authorization: Bearer <access_token>
    """
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
