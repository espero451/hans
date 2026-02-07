-- MASTER:

CREATE TABLE owners ( 
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    comment TEXT
);

CREATE TABLE patients ( 
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    species TEXT NOT NULL,
    owner_id  INT NOT NULL REFERENCES owners(id),
    breed TEXT,
    birth_date DATE
);

CREATE TABLE specimen_types ( 
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,  
    name TEXT NOT NULL,
    tube TEXT,
    description TEXT
);

CREATE TABLE test_catalog (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,   
    specimen_type_id INT NOT NULL REFERENCES specimen_types(id),
    description TEXT,
    price NUMERIC(10,2) NOT NULL
);

CREATE TABLE instruments (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    model TEXT,
    location TEXT
);

CREATE TABLE workstations ( 
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    instrument_id INT REFERENCES instruments(id)
);

CREATE TABLE service_catalog (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC(10,2) NOT NULL
);

-- RUNTIME:

CREATE SEQUENCE specimen_barcode_seq;

-- orders
--   ├─ specimens
--   ├─ test_runs
--   ├─ service_runs
--   └─ results → test_runs = 1:N

CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    patient_id INT NOT NULL REFERENCES patients(id),
    created_by INT REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    archived BOOLEAN DEFAULT false,
    comment TEXT
);

CREATE TYPE specimen_status AS ENUM (
  'NEW',
  'COLLECTED',
  'RECEIVED',
  'CANCELED'
);

CREATE TABLE specimens ( 
    specimen_id TEXT PRIMARY KEY, 
    order_id INT NOT NULL REFERENCES orders(id),
    specimen_type_id INT NOT NULL REFERENCES specimen_types(id),
    status specimen_status NOT NULL DEFAULT 'NEW',
    collected_at timestamptz,
    received_at timestamptz
);

CREATE TYPE test_run_status AS ENUM (
  'NEW', -- NEW
  'SENT', -- SENT (downloaded) to instrument
  'RECEIVED'  -- result received
);

CREATE TABLE test_runs (
    id BIGSERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    test_catalog_id INT NOT NULL REFERENCES test_catalog(id),
    specimen_id TEXT NOT NULL REFERENCES specimens(specimen_id),
    workstation_id INT REFERENCES workstations(id),
    instrument_id INT REFERENCES instruments(id),
    status test_run_status NOT NULL DEFAULT 'NEW',
    price NUMERIC(10,2) NOT NULL -- copy here price from test_catalog (to fix price at the moment of ordering)
);

CREATE TYPE service_run_status AS ENUM (
  'NEW',
  'COMPLETED',
  'CANCELED'
);

CREATE TABLE service_runs (
    id BIGSERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    service_catalog_id INT NOT NULL REFERENCES service_catalog(id),
    status service_run_status NOT NULL DEFAULT 'NEW',
    price NUMERIC(10,2) NOT NULL,  -- snapshot
    completed_at timestamptz
);

CREATE TABLE results (
    id BIGSERIAL PRIMARY KEY,
    test_run_id BIGINT NOT NULL REFERENCES test_runs(id),
    value TEXT,
    units TEXT,
    flags TEXT,
    completed_at timestamptz,
    verified BOOLEAN DEFAULT false
);

CREATE INDEX ON test_runs(order_id);
CREATE INDEX ON test_runs(specimen_id);
CREATE INDEX ON results(test_run_id);
CREATE INDEX ON service_runs(order_id);
CREATE INDEX ON test_runs(status);
CREATE INDEX ON service_runs(status);
CREATE INDEX ON specimens(status);
CREATE INDEX ON specimens(order_id);
CREATE INDEX ON orders(patient_id);

CREATE UNIQUE INDEX ux_specimen_per_type
ON specimens(order_id, specimen_type_id);
