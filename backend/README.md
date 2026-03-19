# Backend

## Run API

```bash
poetry run uvicorn hans.main:app --reload
```

## Run Integration Tests

Integration tests use a dedicated database URL from `TEST_DATABASE_URL`.
If it is not set, tests in `tests/integration` are skipped.

```bash
TEST_DATABASE_URL='postgresql+asyncpg://hans:hans@127.0.0.1:5433/hans_test' poetry run pytest tests/integration -q
```
