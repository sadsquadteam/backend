# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UniFound Backend is a Django REST Framework application implementing JWT-based email authentication with OTP verification. The system has 95+ comprehensive unit tests covering models, serializers, and API endpoints.

## Tech Stack

- **Framework**: Django 6.0
- **API**: Django REST Framework 3.16.1
- **Authentication**: djangorestframework-simplejwt 5.3.1
- **Documentation**: drf-spectacular 0.27.2
- **Database**: SQLite3 (development)
- **Python**: 3.13

## Project Structure

```
base/                # Django project configuration
├── settings.py      # Django settings (JWT, DRF, email, cache config)
├── urls.py          # Root URL routing (/api/users/, /api/docs/, etc.)
├── wsgi.py / asgi.py

users/               # Main app - handles all authentication
├── models.py        # CustomUser (extends AbstractUser, email-based), TokenBlacklist (logout tracking)
├── views.py         # 7 function-based views: register, verify_email, login, refresh_token, logout, profile, change_password
├── serializers.py   # Request/response validation
├── urls.py          # User endpoint routing
├── validators.py    # Password complexity validation
├── utils.py         # OTP generation, storage, email sending
├── admin.py         # Django admin configuration
└── tests/           # 95+ unit tests
    ├── test_models.py       # Model and manager tests
    ├── test_serializers.py  # Validation tests
    └── test_views.py        # Endpoint integration tests
```

## Core Architecture Concepts

### Authentication Flow
1. **Register** (`POST /api/users/register/`) - Email only, triggers OTP email (5 min validity, 3 attempts max)
2. **Verify** (`POST /api/users/verify/`) - OTP + password, creates verified user
3. **Login** (`POST /api/users/login/`) - Returns access token (15 min) + refresh token (7 days)
4. **Use API** - Include `Authorization: Bearer <access_token>` header
5. **Refresh** (`POST /api/users/refresh/`) - Get new access token
6. **Logout** (`POST /api/users/logout/`) - Blacklist refresh token

### Key Design Decisions
- **Email-based Login**: CustomUser uses email as USERNAME_FIELD (not Django's default username)
- **OTP Verification**: Uses Django cache (locmem in dev) for time-limited OTP storage with attempt tracking
- **Token Blacklisting**: TokenBlacklist model with indexed queries (refresh_token, expires_at) for logout
- **Cache-Heavy**: OTP, attempts, and registration state stored in cache (no database writes until verify)
- **Function-Based Views**: Simple @api_view decorators with @permission_classes for cleaner auth logic

### Security Configuration
- Password: 8+ chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char (!@#$%^&*)
- JWT: HS256 algorithm using SECRET_KEY
- Password hashing: Django's PBKDF2 (AbstractUser default)
- Token blacklist: Indexed queries + expires_at field for cleanup
- Proper HTTP codes: 400 (validation), 401 (auth), 404 (not found)

## Common Development Commands

```bash
# Setup & activate environment
python3.13 -m venv venv_py313
source venv_py313/bin/activate
pip install -r requirements.txt

# Database
python manage.py migrate
python manage.py makemigrations

# Run all tests (95 tests)
python manage.py test users.tests.test_models users.tests.test_serializers users.tests.test_views

# Run single test class
python manage.py test users.tests.test_views.UserRegistrationEndpointTests

# Run single test
python manage.py test users.tests.test_views.UserRegistrationEndpointTests.test_register_with_valid_email

# Development server
python manage.py runserver

# Django shell (interactive)
python manage.py shell

# Create superuser
python manage.py createsuperuser --email admin@uni.edu
```

## API Endpoints Reference

All endpoints under `/api/users/`:

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `register/` | No | Send OTP to email |
| POST | `verify/` | No | Verify OTP + set password |
| POST | `login/` | No | Get JWT tokens |
| POST | `refresh/` | No | Get new access token |
| POST | `logout/` | Yes | Blacklist refresh token |
| GET | `profile/` | Yes | Get authenticated user |
| PUT | `change-password/` | Yes | Update password |

## Important Implementation Details

### CustomUserManager (users/models.py:9-29)
- `create_user()`: Sets email as username to avoid duplicate username issues
- `create_superuser()`: Delegates to create_user with is_staff/is_superuser flags

### OTP System (users/utils.py)
- Generated as 6-digit numeric code, cached with email key: `otp_{email}`
- Attempt counter stored as `attempts_{email}`
- 5-minute expiry, max 3 attempts before blocking
- Must call `verify_otp()` before password creation in serializer

### Token Blacklisting Strategy (users/models.py:55-78)
- Refresh tokens blacklisted on logout (TokenBlacklist model)
- Indexed on refresh_token and expires_at for efficient queries
- Check blacklist in verify_refresh_token logic (not automatic in SimpleJWT)
- Consider cronjob for cleaning expired tokens (expires_at < now)

### Testing Pattern (users/tests/)
- Use `APIClient` for endpoint testing
- Call `cache.clear()` in setUp/tearDown for isolation
- Test both happy path and error cases
- Verify serializer validation and HTTP status codes

## Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Schema**: http://localhost:8000/api/schema/ (OpenAPI JSON)
- Powered by drf-spectacular with AutoSchema

## Pre-Deployment Checklist

These are in base/settings.py - change before production:
- Set `DEBUG = False`
- Move `SECRET_KEY` to environment variable (not hardcoded)
- Configure `ALLOWED_HOSTS` with actual domain
- Switch `EMAIL_BACKEND` from console to SMTP (AWS SES, SendGrid, etc.)
- Change database from SQLite to PostgreSQL/MySQL
- Enable HTTPS/SSL
- Consider rate limiting middleware for brute-force protection

## Cache Configuration

Current: In-memory LocMemCache (development only). For production:
- Switch to Redis cache for distributed/multi-process deployments
- OTP operations: `cache.get/set(f'otp_{email}', otp_data, timeout=300)`
- Attempt tracking: `cache.get/increment(f'attempts_{email}')`
