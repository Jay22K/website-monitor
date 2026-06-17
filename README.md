# Website Monitor

A production-ready website uptime monitoring service built with **FastAPI**, **PostgreSQL**, and **APScheduler**.

Tracks registered websites, exposes REST endpoints for on-demand checks, and sends a **daily email report** at 10:00 AM automatically.

---

## Tech Stack

| Layer           | Choice            |
|-----------------|-------------------|
| API             | FastAPI            |
| Database        | PostgreSQL 16      |
| ORM             | SQLAlchemy (async) |
| Migrations      | Alembic            |
| Scheduler       | APScheduler        |
| HTTP Client     | httpx              |
| Email           | SMTP (Gmail)       |
| Containerization| Docker Compose     |
| Testing         | pytest             |

---

## Quick Start (Docker)

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd website-monitor

# 2. Configure environment
cp .env.example .env
# Edit .env — fill in SMTP_USER, SMTP_PASSWORD, EMAIL_TO for email reports

# 3. Build and start
docker compose up --build

# 4. App is live at http://localhost:8000
# 5. Swagger UI at http://localhost:8000/docs
```

---

## Local Development (without Docker)

```bash
# Prerequisites: Python 3.12+, PostgreSQL running locally

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# setup DB server in system
install postgresql in PC/Laptop/System
Setup postgresql 

# Set env vars (or copy .env.example → .env and edit)
export DATABASE_URL="postgresql+asyncpg://monitor_user:monitor_pass@localhost:5432/website_monitor"

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

---

## API Reference

### `POST /websites` — Add a website

```bash
curl -X POST http://localhost:8000/websites/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Google", "url": "https://google.com"}'
```

Response `201 Created`:
```json
{"id": 1, "name": "Google", "url": "https://google.com", "created_at": "..."}
```

---

### `GET /websites` — List all websites

```bash
curl http://localhost:8000/websites/
```

---

### `POST /websites/{id}/check` — Check a website now

```bash
curl -X POST http://localhost:8000/websites/1/check
```

Response (online):
```json
{
  "website": "Google",
  "status": "online",
  "http_status_code": 200,
  "response_time_ms": 125.4
}
```

Response (offline):
```json
{
  "website": "Example",
  "status": "offline",
  "http_status_code": null,
  "response_time_ms": null,
  "error_message": "Connection timeout"
}
```

---

### `GET /websites/{id}/results` — Check history

```bash
curl http://localhost:8000/websites/1/results?limit=10
```

---

### `GET /health` — Health check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## Daily Email Report

The scheduler fires every day at **10:00 AM** and:

1. Fetches all registered websites
2. Checks each one concurrently
3. Saves results to the database
4. Generates and emails a report

Example report:

```
==================================================
       Website Monitoring Report
==================================================
Date            : 2026-06-17
Total Websites  : 5
Healthy         : 4
Failed          : 1
--------------------------------------------------
Google                         ONLINE   200
GitHub                         ONLINE   200
OpenAI                         ONLINE   200
ExampleSite                    OFFLINE  Connection timeout
Yahoo                          ONLINE   200
==================================================
```

### Email Configuration (Gmail)

1. Enable 2-Factor Authentication on your Gmail account
2. Create an [App Password](https://myaccount.google.com/apppasswords)
3. Set in `.env`:
   ```
   SMTP_USER=you@gmail.com
   SMTP_PASSWORD=your-app-password
   EMAIL_TO=recipient@example.com
   ```

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx aiosqlite
pytest -v
```

Tests use an **in-memory SQLite** database — no Postgres required for testing.

---

## Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "add is_active column"

# Rollback one step
alembic downgrade -1
```

---

## Project Structure

```
website-monitor/
├── app/
│   ├── api/
│   │   └── websites.py        # REST endpoints
│   ├── db/
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── database.py        # Engine & session factory
│   │   └── migrations/        # Alembic migrations
│   ├── services/
│   │   ├── checker.py         # httpx website checker
│   │   ├── report.py          # Plain-text report builder
│   │   └── email.py           # SMTP email sender
│   ├── scheduler/
│   │   └── jobs.py            # APScheduler daily job
│   ├── schemas/
│   │   └── website.py         # Pydantic request/response models
│   ├── config.py              # Settings via pydantic-settings
│   └── main.py                # FastAPI app + lifespan
├── tests/
│   ├── test_checker.py
│   ├── test_report.py
│   └── test_api.py
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## Design Decisions

**Why APScheduler over Celery?**
For an MVP running inside a single FastAPI process, APScheduler is far simpler to set up — no Redis broker, no separate worker process. It's entirely sufficient for a daily job.

**Why is a 5xx response counted as "online"?**
We received an HTTP response, meaning the server is reachable. A 503 is an application-level problem, not a network outage. This mirrors how most monitoring tools behave.

**Why not use `asyncio` directly for scheduling?**
APScheduler's `BackgroundScheduler` runs in a background thread, which avoids blocking the FastAPI event loop entirely.
