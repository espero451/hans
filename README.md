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
- **Orders**: Create orders for a patient with selected tests and services; `/orders/{id}` returns full order state: specimens, test_runs, service_runs, results.
- **Specimen tracking**: Auto-create runtime specimens (= barcode).
- **Results**: View and update test results (value, units, flags, status, verification); results are stored separately and linked to test_runs (1:N).
- **TCP Server**: LIS listening on a configurable port and dispatching incoming messages to protocol handlers
- **ASTM Handler**:  ASTM message handler for query/result processing; accepts R- and Q-records; returns O-records with test lists.
- **Audit logging**: All CRUD operations are recorded in daily audit logs with user ID and timestamp.
- **Instrument Emulator** (debug tool): Local script for testing ASTM communication without a real analyzer.

## Main Technology Stack

- Python 3.10+
- FastAPI
- SQLAlchemy 2.0 (async ORM)
- asyncpg (PostgreSQL driver)
- Pydantic v2 (schemas and validation)
- PyJWT + passlib (JWT authentication and password hashing)
- Uvicorn (ASGI server)
- Python-dotenv (environment variables)

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

## Quick Start

1. Clone the repository
2. Create `.env` file in `backend/` with at least:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/db_name
SECRET_KEY=your-random-secret-key
```
3. Install dependencies:
```
cd ./hans/backend/
poetry install
```
4. Start the server: `poetry run uvicorn hans.main:app --reload`
5. Open http://localhost:8000/docs for Swagger UI.

Note: Database tables are auto-created on startup. No initial data seeding yet.

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