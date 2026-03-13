<p align="center">
  <img src="frontend/assets/hans.png" alt="Hans LIS" width="150">
</p>


# Hans LIS

Lightweight veterinary Laboratory Information System (LIS). **The project is under active development.**

## Key Features

### Laboratory Workflow

- Veterinary patient and owner management
- Species-aware patient records
- End-to-end laboratory order lifecycle
- Barcode-based specimen tracking
- Test run tracking from order to result
- Result entry and verification

### Analyzer Integration

- ASTM instrument integration over TCP
- Query/response workflow for test requests
- Automatic analyzer result ingestion
- Instrument and workstation management
- Configurable TCP listeners via dispatcher

### Operations & Administration

- JWT authentication with role-based access control
- Built-in admin panel for data management
- Audit logging of critical user actions
- Patient photo upload and media storage
- Network barcode label printing

<p align="center">
  <img src="docs/screenshots/patient.png" alt="Patient" width="100%">
</p>
<p align="center">
  <img src="docs/screenshots/orders.png" alt="Orders" width="100%">
</p>
<p align="center">
  <img src="docs/screenshots/order.png" alt="Order" width="100%">
</p>

<!-- ## Main Functionality

- **Authentication**: JWT-based login, protected endpoints, user roles (admin, staff).
- **CRUD** operations for core entities (owners, patients, specimens, tests, services, orders, results).
- **Orders**: Create orders for a patient with selected tests and services; `/orders/{id}` returns the full order state: specimens, test_runs, service_runs, results.
- **Specimen tracking**: Auto-create runtime specimens (= barcode).
- **Results**: View and update test results (value, units, flags, status, verification); results are stored separately and linked to test_runs (1:N).
- **TCP Server**: LIS listens on multiple configurable ports (from YAML configs) and dispatches incoming messages to protocol handlers.
- **ASTM Handler**: ASTM message handler for query/result processing; accepts R- and Q-records; returns O-records with test lists.
- **Audit logging**: All CRUD operations are recorded in daily audit logs with user ID and timestamp.
- **Instrument Emulator** (debug tool): script for testing ASTM communication without a real analyzer (part of [astmkit](https://github.com/espero451/astmkit)). -->

## Main Technology Stack

### Backend
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

### Frontend
- Vue 3 + Vite
- PrimeVue (UI components)
- Node.js 20+

### Infrastructure & DevOps
- Docker & Docker Compose
- Poetry 2.x (backend dependency management)

## System Architecture

```mermaid
flowchart LR

%% External systems
FE[Frontend SPA]
LAB[Laboratory Analyzers<br/>ASTM over TCP]
PRN[Barcode Printer<br/>TCP 9100]
ADM[Admin User]

%% Backend
subgraph APP[FastAPI Application]
API[REST API]
AUTH[Auth & RBAC<br/>JWT]
ADMIN[Admin Panel<br/>SQLAdmin]
DISPAPI[Dispatcher Admin API]
RUNTIME[Startup / Shutdown Hooks]
end

%% Application layer
subgraph DOMAIN[Application Layer]
SERVICES[Application Services]
REPO[Repositories]
ORM[SQLAlchemy Async ORM]
end

%% Instrument integration
subgraph INSTRUMENTS[Instrument Integration]
DISPATCHER[Dispatcher Service<br/>Background Task]
ENGINE[Dispatcher Engine]
TCP[TCP Listeners]
ASTM[ASTM Protocol Layer<br/>Session + Parser]
CONFIG[YAML Interface Configs]
end

%% Infrastructure
DB[(PostgreSQL)]
TRACE[(Instrument Trace Logs)]
MEDIA[(Patient Media Storage)]

%% Frontend
FE -->|HTTP + JWT| API
ADM --> ADMIN
ADM --> DISPAPI

%% API
API --> AUTH
API --> SERVICES

%% Domain
SERVICES --> REPO
REPO --> ORM
ORM --> DB

%% Media & printing
SERVICES -->|print labels| PRN
SERVICES -->|store photos| MEDIA

%% Admin
ADMIN --> ORM
DISPAPI --> DISPATCHER
RUNTIME --> DISPATCHER

%% Instrument pipeline
DISPATCHER --> ENGINE
ENGINE --> CONFIG
ENGINE --> TCP

LAB <-->|ASTM Messages| TCP
TCP --> ASTM

ASTM -->|Query / Result Events| DISPATCHER
DISPATCHER --> ORM
DISPATCHER --> TRACE
```

## Message Flow: Instrument -> LIS
<details>
<summary>Show diagram</summary>

```mermaid
sequenceDiagram
    autonumber

    participant INS as Laboratory Instrument
    participant TCP as TCP Listener
    participant SES as ASTM Session
    participant ROUTER as Message Router
    participant QUERY as Query Processor
    participant RESULT as Result Processor
    participant DISP as Dispatcher Service
    participant DB as PostgreSQL

    INS->>TCP: TCP connection (ASTM frames)
    TCP->>SES: attach socket stream

    alt Query request (Q records)

        INS->>SES: ASTM Query Message
        SES->>ROUTER: QueryRequested event

        ROUTER->>QUERY: process query
        QUERY->>DISP: load query context (barcodes)

        DISP->>DB: fetch Order / Specimen / TestRun
        DB-->>DISP: context data

        DISP-->>QUERY: query contexts
        QUERY-->>ROUTER: QueryResponsePrepared

        ROUTER-->>SES: build ASTM response
        SES->>INS: Order Response (H/P/O/L)

        QUERY->>DISP: mark test runs as SENT
        DISP->>DB: update test_runs.status

    else Result submission (R records)

        INS->>SES: ASTM Result Message
        SES->>ROUTER: ResultsReceived event

        ROUTER->>RESULT: process results
        RESULT->>DISP: store results

        DISP->>DB: insert results
        DISP->>DB: update test_runs.status = RECEIVED

        DB-->>RESULT: stored result ids

    end

    INS->>TCP: TCP disconnect
```
</details>

## Instrument Pipeline Diagram

```mermaid
flowchart LR

Instrument --> TCP
TCP --> ASTM
ASTM --> Router

Router --> QueryProcessor
Router --> ResultProcessor

QueryProcessor --> Dispatcher
ResultProcessor --> Dispatcher

Dispatcher --> Database
Dispatcher --> TraceLogs
```

## Database Structure (.svg)

<p align="center">
  <img src="docs/schema.svg" alt="Database schema" width="100%">
</p>

## Quick Start 

1. Create `.env` in the project root (used by Docker Compose):
```
POSTGRES_USER=hans
POSTGRES_PASSWORD=hans
POSTGRES_DB=hans
SECRET_KEY=your-secret-key
```
2. Build and start containers:
```
docker compose up -d --build
```
3. Apply migrations:
```
docker compose exec backend alembic upgrade head
```
4. Seed admin user:
```
docker compose exec backend python3 -m hans.tools.seed_admin
```
5. Login with username: `hans`, password: `hans`:
```
http://localhost:8080/login
```

### URLs

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8080`
- Admin UI: `http://localhost:8000/admin` (CRUD management for all database entities)

### Notes

- Docker uses `network_mode: host` for the backend to expose dynamic instrument ports.
  This works only on Linux. For Docker Desktop (macOS/Windows), a different setup
  is required (no host networking).
<!-- - `/.env` is used by Docker Compose for container environment variables. -->
<!-- - `backend/.env` is used for local backend runs (when you start FastAPI directly).
  For local runs, start the backend from the `backend/` directory to ensure the
  correct `.env` is loaded. -->

### Ports

- Postgres is exposed to the host on `5433` (`db` container port `5432`).
- Frontend is exposed on `8080`.
- Instrument interface ports come from YAML configs in
  `backend/src/hans/interfaces/configs` (for example `20100`, `20200`).
  Because `backend` uses `network_mode: host` in Docker, these ports are
  listened on directly by the host with no Docker port mapping.

## Instrument Interfaces

Configuration files live in `backend/src/hans/interfaces/configs`. Each config defines interface name, host, port, and test codes translation.

### Instrument Emulator (astmkit)

You can use [astmkit](https://github.com/espero451/astmkit) to simulate input from instrument.
It sends an ASTM frame over TCP to a target host and prints response frames.

```
astmkit inst input.astm --port 20100
```

Make sure the emulator port matches one of the configured interface ports (`port` in the YAML configs at `backend/src/hans/interfaces/configs`).

### Dispatcher

The dispatcher is a background TCP listener that loads YAML configs, opens
instrument ports, and routes incoming messages to the appropriate protocol
handlers.

Dispatcher starts automatically with the backend.

- Dispatcher status: `GET /settings/dispatcher/status`
- Dispatcher restart: `POST /settings/dispatcher/restart`

## Logs and Traces

- Audit logs: `live/audit/YYYY-MM-DD.log`
- Instrument traces: `live/instruments/<interface>/<YYYY-MM-DD>/`

## Tests

### Run tests in Docker

Run all tests:
```
docker compose exec backend sh -lc "cd /app/backend && PYTHONPATH=src pytest -q"
```

Run a single test file:
```
docker compose exec backend sh -lc "cd /app/backend && PYTHONPATH=src pytest -q tests/unit/test_orders_print_specimen.py"
```

# Roadmap

- Order-level comments for services
- PDF lab reports
- Reference ranges
- Analyzer management UI
- Add more tests


(*In memory of Hans, a cat who was lost and never came back.*)
