"""
URL configuration for users app.
"""
from django.urls import path
from users.views import (
    register,
    verify_email,
    login,
    refresh_token,
    logout,
    profile,
    change_password,
)

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', register, name='register'),
    path('auth/verify/', verify_email, name='verify'),
    path('auth/login/', login, name='login'),
    path('auth/refresh/', refresh_token, name='refresh'),
    path('auth/logout/', logout, name='logout'),
    path('auth/profile/', profile, name='profile'),
    path('auth/change-password/', change_password, name='change-password'),
]
