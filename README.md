# Hotel Reservation System

A production-minded Django REST API for hotel inventory, guest reservations, check-in workflows, and payments.

## Highlights

- Guest self-registration and rotating token authentication
- Admin, receptionist, and guest roles with object-level data isolation
- Room types and room inventory management
- Transactional availability checks that reject overlapping stays
- Server-calculated rate snapshots and reservation totals
- Enforced booking, check-in, check-out, and cancellation state transitions
- Balance-aware payment recording and an operational dashboard
- PostgreSQL 18 deployment path, Docker Compose, migrations, seed data, and CI

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py runserver
```

SQLite is used by default. Copy `.env.example` and set PostgreSQL variables for a production-style environment, or run `docker compose up --build`.

Development users created by `seed` are `admin`, `reception`, and `guest`, all with password `ChangeMe123!`. Change these credentials outside local development.

## API

Authenticate using `Authorization: Token <token>`.

| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/auth/register/` | Public guest registration |
| POST | `/api/auth/login/` | Public |
| POST | `/api/auth/logout/` | Authenticated |
| GET | `/api/auth/me/` | Authenticated |
| GET/POST | `/api/room-types/` | Read authenticated; write staff |
| GET/POST | `/api/rooms/` | Read authenticated; write staff |
| GET/POST | `/api/reservations/` | Authenticated; guests scoped to themselves |
| PATCH | `/api/reservations/{id}/transition/` | Staff |
| POST | `/api/reservations/{id}/payment/` | Staff |
| GET | `/api/dashboard/` | Staff |

Collection endpoints are paginated and support search/ordering. Reservations accept a `status` query filter; rooms accept `active`.

## Quality checks

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
pip check
```

Tests cover forced guest registration, server-controlled ownership/pricing, overlapping-room protection, object ownership, and overpayment prevention. CI repeats migrations, seeding, checks, tests, and dependency validation against PostgreSQL.

## Security notes

Passwords use Django validation and hashing. Login is throttled and rotates tokens. Role checks protect staff mutations; guest querysets enforce ownership. Price, total, creator, and state fields are server controlled. Availability and payment balance decisions lock relevant rows inside database transactions. Configure a strong secret, HTTPS, production hosts, and restricted CORS origins before deployment.

## License

MIT
