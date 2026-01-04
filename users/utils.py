"""
Utility functions for authentication.
"""
import random
import string
from django.core.cache import cache


def generate_otp(length=6):
    """
    Generate a random OTP of specified length.

    Args:
        length: Length of OTP (default: 6)

    Returns:
        String of random digits
    """
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(email, otp):
    """
    Send OTP to user's email.

    Args:
        email: User's email address
        otp: OTP to send

    Note:
        Uses Django's email backend configured in settings.
        For development, uses console backend that prints to stdout.
    """
    from django.core.mail import send_mail

    subject = 'Your OTP for UniFound Account Verification'
    message = f'''
    Hello,

    Your OTP for email verification is: {otp}

    This OTP is valid for 5 minutes.

    If you didn't request this, please ignore this email.

    Best regards,
    UniFound Team
    '''

    send_mail(
        subject,
        message,
        'noreply@unifound.local',
        [email],
        fail_silently=True,
    )


def store_otp(email, otp, ttl=300):
    """
    Store OTP in cache.

    Args:
        email: User's email address
        otp: OTP to store
        ttl: Time to live in seconds (default: 300 = 5 minutes)
    """
    cache_key = f'otp_{email}'
    otp_data = {
        'otp': otp,
        'attempts': 0,
        'created_at': __import__('django.utils.timezone', fromlist=['now']).now().isoformat()
    }
    cache.set(cache_key, otp_data, ttl)


def verify_otp(email, otp, max_attempts=3):
    """
    Verify OTP from cache.

    Args:
        email: User's email address
        otp: OTP to verify
        max_attempts: Maximum verification attempts (default: 3)

    Returns:
        Tuple (success: bool, message: str)
    """
    cache_key = f'otp_{email}'
    otp_data = cache.get(cache_key)

    if not otp_data:
        return False, 'OTP has expired or not found.'

    attempts = otp_data.get('attempts', 0)
    if attempts >= max_attempts:
        cache.delete(cache_key)
        return False, 'Maximum OTP verification attempts exceeded.'

    if otp_data['otp'] != otp:
        otp_data['attempts'] = attempts + 1
        cache.set(cache_key, otp_data, 300)
        return False, 'Invalid OTP.'

    # OTP is valid, remove from cache
    cache.delete(cache_key)
    return True, 'OTP verified successfully.'


def get_otp(email):
    """
    Get OTP from cache without verifying.

    Args:
        email: User's email address

    Returns:
        OTP string or None if not found
    """
    cache_key = f'otp_{email}'
    otp_data = cache.get(cache_key)

    if otp_data:
        return otp_data.get('otp')
    return None


def delete_otp(email):
    """
    Delete OTP from cache.

    Args:
        email: User's email address
    """
    cache_key = f'otp_{email}'
    cache.delete(cache_key)
