# UniFound Backend API

Django REST backend for authentication, lost/found items, comments, and reports.

## Quick Start
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Local base URL: `http://127.0.0.1:8000`

## API Docs
- Swagger: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI: `http://127.0.0.1:8000/api/schema/`

## Auth Model
- JWT bearer token:
  - `Authorization: Bearer <access_token>`
- Access token lifetime: `15 min`
- Refresh token lifetime: `7 days`

## Main API Groups
- `api/users/` -> registration, verification, login, token refresh/logout, profile, password change
- `api/items/` -> item CRUD + tags
- `api/interactions/` -> comments + reports

---

## Users API
Base path: `/api/users/`

- `POST register/` (public)
  - body: `{ "email": "user@example.com" }`
  - sends OTP to email (user is created on verify)
- `POST verify/` (public)
  - body: `{ "email": "user@example.com", "otp": "123456", "password": "SecurePass123!" }`
  - verifies OTP and creates verified user
- `POST login/` (public)
  - body: `{ "email": "user@example.com", "password": "SecurePass123!" }`
  - response includes `access` and `refresh`
- `POST refresh/` (public)
  - body: `{ "refresh": "<refresh_token>" }`
  - returns new access token
- `POST logout/` (auth)
  - body: `{ "refresh": "<refresh_token>" }`
  - blacklists refresh token
- `GET profile/` (auth)
- `PUT change-password/` (auth)
  - body: `{ "old_password": "...", "new_password": "..." }`

Password policy:
- min 8 chars, uppercase, lowercase, digit, special char from `!@#$%^&*`

---

## Items API
Base path: `/api/items/`

### Endpoints
- `GET /` (public): list items
- `POST /` (auth): create item
- `GET /{id}/` (public): retrieve item
- `PUT/PATCH /{id}/` (auth, owner-only): update
- `DELETE /{id}/` (auth, owner-only): delete
- `GET /tags/` (public): list tags

### Item fields
```json
{
  "id": 1,
  "title": "Lost Wallet",
  "description": "Near library",
  "latitude": 35.7,
  "longitude": 51.3,
  "image": null,
  "tags": [1, 5],
  "status": "lost"
}
```

### List filters/query
- `status=lost|found|delivered`
- `creator=<user_id>`
- `tags=<tag_id>`
- `tags__title=<exact>`
- `tags__title__icontains=<text>`
- `created_at__gt|gte|lt|lte=<datetime>`
- `search=<text>` on `title` and `description`
- `ordering=created_at` or `ordering=-created_at`

Notes:
- `creator` is set automatically from the authenticated user.
- owner-only update/delete returns `404` for non-owner.

---

## Interactions API
Base path: `/api/interactions/`

### Comments
- `GET comments/` (auth)
- `POST comments/` (auth)
- `GET comments/{id}/` (auth)
- `PUT/PATCH comments/{id}/` (auth, owner-only)
- `DELETE comments/{id}/` (auth, owner-only)

Create comment body:
```json
{
  "item": 12,
  "text": "I think this is mine",
  "replies_to": null
}
```

Response fields: `id`, `user`, `item`, `text`, `replies_to`, `created_at`

### Reports
- `POST reports/` (auth)

Create report body (exactly one target):
```json
{ "item": 12, "reason": "spam" }
```
or
```json
{ "comment": 45, "reason": "abuse" }
```

Validation rules:
- provide exactly one target (`item` xor `comment`)
- duplicate report from same user on same target is rejected

Moderation rule:
- when a target gets more than 5 reports, it is auto-deleted on the 6th report
  - item target -> item deleted
  - comment target -> comment deleted

---

## Status Codes
- `200` success
- `201` created
- `204` deleted
- `400` validation error
- `401` unauthorized
- `404` not found / owner-scoped missing

## Frontend Integration Notes
- DRF pagination is enabled globally (`count`, `next`, `previous`, `results`).
- CORS currently allows:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
- Use `multipart/form-data` for item create/update when uploading `image`.

## Recommended Client Flow
1. Register email (`/api/users/register/`)
2. Verify OTP + password (`/api/users/verify/`)
3. Login (`/api/users/login/`)
4. Call protected APIs with access token
5. Refresh token when needed (`/api/users/refresh/`)
6. Logout (`/api/users/logout/`)
