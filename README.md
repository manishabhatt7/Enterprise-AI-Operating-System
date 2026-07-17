# AIOS

AIOS is a FastAPI-based backend starter for managing organizations and users. It provides JWT-based authentication, PostgreSQL persistence, Redis-backed session storage, and a clean API structure for building multi-tenant applications.

## What this project does

This project includes:

- User registration, login, refresh, logout, and profile retrieval
- Organization creation and management
- Async SQLAlchemy models with PostgreSQL
- Redis-backed refresh-session storage
- Alembic database migrations
- Swagger/OpenAPI documentation via FastAPI
- Health checks and structured API responses

## Tech stack

- Python 3.11
- FastAPI
- SQLAlchemy 2.x with asyncpg
- PostgreSQL
- Redis
- Alembic
- Pydantic Settings
- Pytest

## Project structure

- app/main.py: FastAPI application entrypoint
- app/api/v1/: API routes and endpoints
- app/services/: business logic
- app/models/: SQLAlchemy models
- app/repositories/: data access layer
- app/cache/: Redis session storage
- app/core/: config, JWT, security, logging
- alembic/: database migrations
- tests/: automated tests

## Prerequisites

Before running the project, make sure you have:

- Python 3.11+
- Docker and Docker Compose (recommended)
- A local PostgreSQL and Redis instance, or Docker Compose services

## Environment configuration

1. Copy the example environment file:

   ```bash
   copy .env.example .env
   ```

   On Linux/macOS:

   ```bash
   cp .env.example .env
   ```

2. Update the values in .env as needed.

   Key variables include:

   - DATABASE_URL
   - JWT_SECRET_KEY
   - JWT_ALGORITHM
   - REDIS_HOST and REDIS_PORT

## Running with Docker Compose (recommended)

This is the easiest way to run the full stack with PostgreSQL and Redis.

```bash
docker compose up --build
```

The API will be available at:

- http://localhost:8000/docs for Swagger UI
- http://localhost:8000/redoc for ReDoc

Run database migrations:

```bash
docker compose exec backend alembic upgrade head
```

To stop the stack:

```bash
docker compose down
```

## Running locally without Docker

### 1) Create and activate a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
uv sync
```

### 3) Start PostgreSQL and Redis

If you are not using Docker, make sure PostgreSQL and Redis are running and reachable from the values in .env.

### 4) Run database migrations

```bash
alembic upgrade head
```

### 5) Start the API server

```bash
uvicorn app.main:app --reload
```

The API will then be available at:

- http://127.0.0.1:8000/docs

## API overview

### Health

- GET /api/v1/health/health

### Authentication

- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me

### Organizations

- POST /api/v1/organizations
- GET /api/v1/organizations
- GET /api/v1/organizations/{organization_id}
- PATCH /api/v1/organizations/{organization_id}
- DELETE /api/v1/organizations/{organization_id}

## Example requests

### Register a user

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "full_name": "John Doe",
    "email": "john@example.com",
    "password": "strongpassword"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "strongpassword"
  }'
```

## Running tests

```bash
pytest -q
```

The current test suite passes successfully with the existing project configuration.

