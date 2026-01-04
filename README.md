# UniFound Backend API

JWT-based authentication system using Django REST Framework.

## Quick Start

```bash
# Setup
python3.13 -m venv venv_py313
source venv_py313/bin/activate
pip install -r requirements.txt
python manage.py migrate

# Run tests (95 tests total)
python manage.py test users.tests.test_models users.tests.test_serializers users.tests.test_views

# Run server
python manage.py runserver  # http://localhost:8000/
```

## API Endpoints

Base URL: `/api/users/`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/register/` | Register user, send OTP to email | No |
| POST | `/verify/` | Verify OTP, set password | No |
| POST | `/login/` | Login, get JWT tokens | No |
| POST | `/refresh/` | Refresh access token | No |
| POST | `/logout/` | Logout, blacklist token | Yes |
| GET | `/profile/` | Get user profile | Yes |
| PUT | `/change-password/` | Change password | Yes |

## Authentication Flow

1. Register → Email + OTP sent
2. Verify → Confirm OTP + set password
3. Login → Get access + refresh tokens
4. Use API → Header: `Authorization: Bearer <access_token>`
5. Refresh → Use refresh token when access expires
6. Logout → Blacklist refresh token

## API Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Configuration

**Password Requirements:**
- 8+ characters, 1 uppercase, 1 lowercase, 1 digit, 1 special char (!@#$%^&*)
- Example: `SecurePass123!`

**Token Lifetimes:**
- Access Token: 15 minutes
- Refresh Token: 7 days
- OTP Valid: 5 minutes, Max 3 attempts

**User Model Fields:**
- `email` (unique, login field)
- `password` (hashed PBKDF2)
- `is_verified` (email verified)
- `is_active` (account status)
- `created_at` (timestamp)

## Security

- JWT HS256 with SECRET_KEY signing
- PBKDF2 password hashing
- OTP email verification with attempt limiting
- Token blacklisting on logout (indexed)
- Proper HTTP codes (400 validation, 401 auth)
- No sensitive info in error messages

## Status Codes

- `200` - Success
- `400` - Validation error
- `401` - Authentication error
- `404` - Not found

## Architecture

```
users/
├── models.py          # CustomUser, TokenBlacklist
├── serializers.py     # Request/response validation
├── views.py           # 7 API endpoints
├── urls.py            # Routing (/api/users/...)
├── validators.py      # Password complexity validation
├── utils.py           # OTP generation/verification
├── admin.py           # Admin panel config
└── tests/             # 95 unit tests
    ├── test_models.py
    ├── test_serializers.py
    └── test_views.py
```

## Production Setup

Before deployment:
1. Set `DEBUG = False` in settings
2. Move `SECRET_KEY` to `.env` (use environment variable)
3. Configure `ALLOWED_HOSTS` with your domain
4. Setup email backend (SMTP, not console)
5. Use production database (not SQLite)
6. Enable HTTPS/SSL
7. Consider rate limiting middleware

## curl Examples

```bash
# Register
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@uni.edu"}'

# Login
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@uni.edu","password":"SecurePass123!"}'

# Get Profile
curl -X GET http://localhost:8000/api/users/profile/ \
  -H "Authorization: Bearer <access_token>"
```
