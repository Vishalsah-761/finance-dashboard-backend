# Finance Dashboard Backend

A role-based finance record management API built with **Python Flask** and **MongoDB**.

---

## Why I Built This

I wanted to learn how real backend systems handle:
- authentication (JWT)
- role-based access control
- scalable API architecture

This project helped me understand how production APIs are structured.

---

## Table of Contents
1. [Tech Stack](#tech-stack)
2. [Architecture Overview](#architecture-overview)
3. [Role & Permission Model](#role--permission-model)
4. [Project Structure](#project-structure)
5. [Quick Start](#quick-start)
6. [Running Tests](#running-tests)
7. [API Reference](#api-reference)
8. [Data Models](#data-models)
9. [Assumptions & Tradeoffs](#assumptions--tradeoffs)

---

## Tech Stack

| Layer        | Choice                             | Reason                                              |
|--------------|------------------------------------|-----------------------------------------------------|
| Framework    | Flask 3.0                          | Lightweight, explicit, easy to reason about         |
| Database     | MongoDB (via PyMongo / Flask-PyMongo) | Flexible schema, native aggregation pipeline      |
| Auth         | JWT (flask-jwt-extended)           | Stateless, suits dashboard API consumption          |
| Passwords    | bcrypt (flask-bcrypt)              | Industry-standard adaptive hashing                  |
| Validation   | Marshmallow                        | Declarative schemas, clean error messages           |
| Tests        | pytest + mongomock                 | Fast unit tests with no real DB required            |

---

## Architecture Overview

```
finance-backend/
├── app/
│   ├── __init__.py          # App factory + extension init
│   ├── config.py            # Config classes (dev / test)
│   ├── models/              # Schema definitions + serializers
│   │   ├── user.py
│   │   └── record.py
│   ├── services/            # All business logic lives here
│   │   ├── user_service.py
│   │   └── record_service.py
│   ├── routes/              # Thin HTTP layer (validates → calls service → responds)
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── records.py
│   │   └── dashboard.py
│   ├── middleware/
│   │   ├── auth.py          # JWT decorators (require_auth, require_role, require_active)
│   │   └── schemas.py       # Marshmallow input schemas
│   └── utils/
│       ├── constants.py     # Role, RecordType, categories enums
│       ├── responses.py     # Consistent JSON response helpers
│       └── pagination.py    # Reusable pagination logic
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_records.py
│   └── test_dashboard.py
├── run.py                   # Entry point
├── seed.py                  # Seed DB with demo users + records
├── requirements.txt
└── .env.example
```

**Key design principle:** Routes are intentionally thin — they only parse the request, call a service method, and format the response. All business logic (queries, aggregations, validation rules) lives in `services/`.

---

## Role & Permission Model

| Action                         | Viewer | Analyst | Admin |
|--------------------------------|:------:|:-------:|:-----:|
| Login / register               | ✅     | ✅      | ✅    |
| View own profile               | ✅     | ✅      | ✅    |
| List / get financial records   | ✅     | ✅      | ✅    |
| View recent activity           | ✅     | ✅      | ✅    |
| Dashboard summary & trends     | ❌     | ✅      | ✅    |
| Category breakdown             | ❌     | ✅      | ✅    |
| Create financial records       | ❌     | ❌      | ✅    |
| Update / delete records        | ❌     | ❌      | ✅    |
| Manage users (CRUD)            | ❌     | ❌      | ✅    |

Enforcement is done via `@require_role(...)` and `@require_active` decorators applied at the route level — not inline if-statements.

---

## Quick Start

### Prerequisites
- Python 3.11+
- MongoDB running on `localhost:27017` (or set `MONGO_URI` in `.env`)

### 1. Clone & install
```bash
git clone <repo-url>
cd finance-backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — at minimum set a strong JWT_SECRET_KEY
```

### 3. Seed the database (optional but recommended)
```bash
python seed.py
```
This creates three users and 15 sample records:

| Role    | Email                    | Password    |
|---------|--------------------------|-------------|
| Admin   | admin@finance.dev        | admin123    |
| Analyst | analyst@finance.dev      | analyst123  |
| Viewer  | viewer@finance.dev       | viewer123   |

### 4. Run
```bash
python run.py
# API available at http://localhost:5000
```

---

## Running Tests

Tests use `mongomock` — **no real MongoDB needed**.

```bash
pytest tests/ -v
```

---

## API Reference

All responses follow this envelope:

```json
{ "success": true, "message": "...", "data": { ... } }
{ "success": false, "message": "...", "errors": { ... } }
```

### Authentication

| Method | Path                        | Auth     | Description             |
|--------|-----------------------------|----------|-------------------------|
| POST   | `/api/auth/register`        | None     | Register new user       |
| POST   | `/api/auth/login`           | None     | Login, receive JWT      |
| GET    | `/api/auth/me`              | JWT      | Get own profile         |
| POST   | `/api/auth/change-password` | JWT      | Change own password     |

**Register / Login body:**
```json
{ "username": "alice", "email": "alice@example.com", "password": "secret123" }
```

**Login response:**
```json
{
  "success": true,
  "data": {
    "access_token": "<jwt>",
    "user": { "id": "...", "username": "alice", "role": "viewer", "status": "active" }
  }
}
```

Pass the token as: `Authorization: Bearer <token>`

---

### Users  *(Admin only)*

| Method | Path               | Description                      |
|--------|--------------------|----------------------------------|
| GET    | `/api/users/`      | List users (filter: role, status)|
| POST   | `/api/users/`      | Create user                      |
| GET    | `/api/users/:id`   | Get user by ID                   |
| PATCH  | `/api/users/:id`   | Update role or status            |
| DELETE | `/api/users/:id`   | Delete user                      |

**Query params for list:** `role`, `status`, `page`, `limit`

**PATCH body:**
```json
{ "role": "analyst", "status": "inactive" }
```

---

### Financial Records

| Method | Path                  | Auth          | Description                     |
|--------|-----------------------|---------------|---------------------------------|
| GET    | `/api/records/`       | Any active    | List records (filterable)       |
| POST   | `/api/records/`       | Admin only    | Create record                   |
| GET    | `/api/records/:id`    | Any active    | Get record by ID                |
| PATCH  | `/api/records/:id`    | Admin only    | Update record                   |
| DELETE | `/api/records/:id`    | Admin only    | Soft-delete record              |

**Query params for list:**
- `type` — `income` or `expense`
- `category` — any valid category (see below)
- `date_from` / `date_to` — `YYYY-MM-DD`
- `search` — searches notes and category
- `page`, `limit`

**Create / update body:**
```json
{
  "amount": 1500.00,
  "type": "income",
  "category": "salary",
  "date": "2024-03-15",
  "notes": "March salary"
}
```

**Valid categories:**
`salary`, `freelance`, `investment`, `gift`, `other_income`,
`food`, `transport`, `housing`, `utilities`, `healthcare`,
`entertainment`, `education`, `shopping`, `travel`, `other_expense`

---

### Dashboard  *(Analyst + Admin, except recent-activity)*

| Method | Path                              | Description                              |
|--------|-----------------------------------|------------------------------------------|
| GET    | `/api/dashboard/summary`          | Totals: income, expense, net balance     |
| GET    | `/api/dashboard/categories`       | Per-category breakdown                   |
| GET    | `/api/dashboard/monthly-trends`   | Month-by-month income vs expense         |
| GET    | `/api/dashboard/weekly-trends`    | Last N weeks income vs expense           |
| GET    | `/api/dashboard/recent-activity`  | Last N records (all active users)        |

**Query params:**
- `summary` — `date_from`, `date_to`
- `categories` — `type` (income or expense)
- `monthly-trends` — `year`
- `weekly-trends` — `weeks` (default 8, max 52)
- `recent-activity` — `limit` (default 10, max 50)

**Summary response:**
```json
{
  "data": {
    "total_income": 11700.00,
    "total_expenses": 2530.00,
    "net_balance": 9170.00,
    "income_count": 5,
    "expense_count": 10
  }
}
```

**Monthly trends response:**
```json
{
  "data": [
    { "year": 2024, "month": 2, "income": 5000.0, "expense": 1200.0 },
    { "year": 2024, "month": 3, "income": 6700.0, "expense": 1330.0 }
  ]
}
```

---

## Data Models

### User
```
_id        ObjectId
username   string  (unique, lowercase)
email      string  (unique, lowercase)
password   string  (bcrypt hash — never returned in responses)
role       string  viewer | analyst | admin
status     string  active | inactive
created_at datetime
updated_at datetime
```

### Financial Record
```
_id        ObjectId
user_id    string   (ID of the admin who created it)
amount     float    (always positive; type determines sign semantics)
type       string   income | expense
category   string
date       datetime (stored at midnight UTC; returned as YYYY-MM-DD)
notes      string
deleted    bool     (soft-delete flag — deleted records are hidden by default)
created_at datetime
updated_at datetime
```

**MongoDB indexes:**
- `users.email` — unique
- `users.username` — unique
- `records.(user_id, date)` — compound for filtered queries
- `records.category`, `records.type` — for filter performance

---

## Assumptions & Tradeoffs

| Topic                  | Decision                                                                 |
|------------------------|--------------------------------------------------------------------------|
| **Record ownership**   | Records belong to the system, not individual users. `user_id` tracks who *created* the record, not who "owns" it. All active users can read all records. |
| **Soft delete**        | Records are never hard-deleted; `deleted: true` hides them from all queries. Admins could retrieve them with a future `?include_deleted=true` param. |
| **JWT statelessness**  | Tokens carry role + status snapshot. If an admin deactivates a user, their existing token remains valid until it expires (default: 1 hour). A token blocklist (Redis) could fix this for production. |
| **Amount sign**        | Amounts are always stored positive. The `type` field (`income`/`expense`) carries the semantic sign. This avoids sign-convention bugs in aggregations. |
| **Date storage**       | Dates are stored as UTC midnight `datetime` objects for consistent MongoDB aggregation (`$year`, `$month`, `$isoWeek`). The API accepts and returns `YYYY-MM-DD` strings. |
| **Self-protection**    | Admins cannot deactivate or delete their own account (prevents accidental lockout). |
| **Registration roles** | `/api/auth/register` accepts any role in the payload (including `admin`) for demo/seeding simplicity. In production this endpoint would only allow `viewer` self-registration; admin creation would go through `/api/users/`. |
| **Password in JWT**    | The password hash is never included in the JWT identity or any API response. |
| **Rate limiting**      | Not implemented. Would add `flask-limiter` with Redis in production.      |
