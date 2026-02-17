<p align="center">
  <img src="frontend/assets/hans.png" alt="Hans LIS" width="150">
</p>

<!-- > [!CAUTION]
> 🚨 THIS PROJECT IS UNDER ACTIVE DEVELOPMENT. USE AT YOUR OWN RISK. 🚨 -->

# Hans LIS

Lightweight veterinary Laboratory Information System (LIS). **The project is under active development.**

## Overview

Hans LIS provides a REST API to manage core entities in a veterinary laboratory workflow:

- Authentication and user management
- Pet owners and their animals (patients)
- Laboratory specimens, tests, and additional services
- Laboratory orders linking patients to tests/services
- Result entry and status tracking for performed tests
- TCP server and protocol handlers for laboratory instrument integration

<p align="center">
  <img src="docs/screenshots/orders.png" alt="Orders" width="100%">
</p>
<p align="center">
  <img src="docs/screenshots/settings.png" alt="Settings" width="100%">
</p>

## Main Functionality

- **Authentication**: JWT-based login, protected endpoints, user roles (admin, staff).
- **CRUD** operations for core entities (owners, patients, specimens, tests, services, orders, results).
- **Orders**: Create orders for a patient with selected tests and services; `/orders/{id}` returns the full order state: specimens, test_runs, service_runs, results.
- **Specimen tracking**: Auto-create runtime specimens (= barcode).
- **Results**: View and update test results (value, units, flags, status, verification); results are stored separately and linked to test_runs (1:N).
- **TCP Server**: LIS listens on a configurable port and dispatches incoming messages to protocol handlers.
- **ASTM Handler**: ASTM message handler for query/result processing; accepts R- and Q-records; returns O-records with test lists.
- **Audit logging**: All CRUD operations are recorded in daily audit logs with user ID and timestamp.
- **Instrument Emulator** (debug tool): Local script for testing ASTM communication without a real analyzer.

## Main Technology Stack

- Python 3.13+
- FastAPI
- PostgreSQL 16+
- SQLAlchemy 2.0 (async ORM)
- asyncpg (PostgreSQL driver)
- Alembic (migrations)
- Pydantic v2 (schemas and validation)
- python-jose + passlib (JWT authentication and password hashing)
- Uvicorn (ASGI server)
- Python-dotenv (environment variables)
- Vue 3 + Vite (frontend)
- PrimeVue (UI components)
- Poetry 2.x (for backend dev)
- Node.js 20+ (for frontend dev)

## Database Structure (.svg)

<p align="center">
  <img src="docs/schema.svg" alt="Database schema" width="100%">
</p>

<!-- <details>
<summary>Database Structure (.svg)</summary>

<p align="center">
  <img src="docs/schema.svg" alt="Database schema" width="100%">
</p>

</details> -->

## Quick Start (Local Dev)

1. Clone the repository.
2. Create `.env` in `backend/`:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/db_name
SECRET_KEY=your-secret-key
```
3. Install backend dependencies:
```
cd backend
poetry install
```
4. Apply migrations:
```
poetry run alembic upgrade head
```
5. Start the backend:
```
poetry run uvicorn hans.main:app --reload
```
6. Start the frontend:
```
cd ../frontend
npm install
npm run dev
```
7. Open Swagger UI: `http://localhost:8000/docs`
8. Open UI (dev): `http://localhost:5173`

<!-- Note: Database tables are auto-created on startup. No initial data seeding yet. -->

## Database and Migrations

- Migrations live in `backend/migrations`.
- Apply migrations with `poetry run alembic upgrade head`.

## Instrument Interfaces

Start dispatcher (optional TCP instrument server) from `backend/` directory:
```
poetry run python -m hans.interfaces.dispatcher
```

Configuration files live in `backend/src/hans/interfaces/configs`. Each config defines interface name, host, port, and test codes translation.

Instrument emulator:
```
python tools/instrument_emulator.py
```

## Logs and Traces

- Audit logs: `prod/audit/YYYY-MM-DD.log`
- Instrument traces: `prod/instruments/<interface>/<date>/`

# TODO & Current Limitations 

- No reporting and export features
- No tests (unit/integration)
- Minimal input validation beyond Pydantic
- ~~Routers are mounted directly on app instead of using APIRouter (to be refactored)~~
- ~~Write Translation Table functionality~~
- ~~Write instrument-interfaces~~
- ~~No role-based access control (all authenticated users have full access)~~
- ~~No frontend integration yet (CORS configured for http://localhost:5173)~~

(*In memory of Hans, a cat who was lost and never came back.*)