# Hans LIS

Minimalistic Veterinary Laboratory Information System (LIS). Early development stage.

## Overview

Hans LIS provides a REST API to manage core entities in a veterinary laboratory workflow:

- Authentication and user management
- Pet owners and their animals (patients)
- Laboratory specimens, tests, and additional services
- Laboratory orders linking patients to tests/services
- Result entry and status tracking for performed tests

All operations are logged in daily audit files for traceability.

## Main Functionality

- **Authentication**: JWT-based login, protected endpoints
- **CRUD** operations for core entities (owners, patients, specimens, tests, services, orders, results).
- **Orders**: Create orders for a patient with selected tests and services; automatically creates result placeholders
- **Results**: View and (future) update test results (value, units, flags, status, verification)
- **Audit logging**: Every create/update/delete action is recorded with user ID and timestamp

## Technology Stack (Main Components)

- Python 3.10+
- FastAPI
- SQLAlchemy 2.0 (async ORM)
- asyncpg (PostgreSQL driver)
- Pydantic v2 (schemas and validation)
- PyJWT + passlib (JWT authentication and password hashing)
- Uvicorn (ASGI server)
- Python-dotenv (environment variables)

<details>
<summary>Current Database Structure</summary>

PostgreSQL (async engine). Main tables:

- `users`  
  id (PK), username (unique), email, hashed_password, role, created_at

- `owners`  
  id (PK), first_name, last_name, email, phone, comment

- `patients`  
  id (PK), name, species, breed, birth_date, owner_id (FK → owners), created_at

- `specimens`  
  id (PK), name, type, tube, description

- `tests`  
  id (PK), name, description, cost, specimen_id (FK → specimens)

- `services`  
  id (PK), name, description, price

- `orders`  
  id (PK), patient_id (FK → patients), created_by (FK → users), created_at, comment

- `results`  
  id (PK), order_id (FK → orders), test_id (FK → tests), specimen_id (FK → specimens),  
  value, units, flags, specimen_status (N/C/R), collected_at, verified, created_at

- Association tables (many-to-many):  
  `order_tests` (order_id, test_id)  
  `order_services` (order_id, service_id)

Relationships:

- Patient → Owner (many-to-one)
- Test → Specimen (many-to-one)
- Order → Patient (many-to-one)
- Order ↔ Test / Service (many-to-many)
- Result → Order / Test / Specimen (many-to-one)
</details>

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

# Current Limitations & TODO

- Routers are mounted directly on app instead of using APIRouter (to be refactored)
- No pagination on list endpoints (except owners/patients partial)
- No filtering/search on most endpoints
- Result update endpoint missing (only placeholders created on order)
- No role-based access control (all authenticated users have full access)
- No patient/owner search or filtering
- No reporting, statistics, or export features
- No file attachments (e.g., PDFs, images)
- ~~No frontend integration yet (CORS configured for http://localhost:5173)~~
- Minimal input validation beyond Pydantic
- No tests (unit/integration)
- Audit logs are plain files (consider database table or structured logging)
- Write Translation Table functionality
- Write instrument-interfaces

(*In memory of Hans, a cat who was lost and never came back.*)