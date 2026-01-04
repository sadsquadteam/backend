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
    # User authentication and profile endpoints
    path('register/', register, name='register'),
    path('verify/', verify_email, name='verify'),
    path('login/', login, name='login'),
    path('refresh/', refresh_token, name='refresh'),
    path('logout/', logout, name='logout'),
    path('profile/', profile, name='profile'),
    path('change-password/', change_password, name='change-password'),
]
