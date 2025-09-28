# finlite backend

This package contains the CLI-first double-entry ledger core for Finlite.

## Features

- SQLite storage with Alembic migrations
- Typer-based CLI (`fin`)
   - `fin accounts` for chart management
   - `fin txn add` for manual journal entries
   - `fin report cashflow` for income vs. expense summaries
   - `fin export beancount` for interoperability
- Pydantic-powered configuration via `.env`
- Rich logging with structured errors
- Tests, linting, and typing wired in (`pytest`, `ruff`, `mypy`)

### Package layout snapshot

```
finlite/
   cli/        # Typer commands
   core/       # Accounting services
   db/         # Engine, sessions, models
   ingest/     # (Phase 2) bank statement ingestion
   ml/         # (Phase 3) local ML helpers
   nlp/        # (Phase 2A) natural language intents
   reports/    # Reporting utilities
   rules/      # (Phase 2) rules engine
   tui/        # (Phase 2B) Textual UI shell
```

## Getting started

1. Create a virtual environment and install dependencies:

   ```bash
   cd backend
   uv venv  # or python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```

2. Copy the example environment and adjust paths if desired:

   ```bash
   cp ../.env.example ../.env
   ```

3. Initialize the database:

   ```bash
   fin init-db
   ```

4. Run the test suite and linters:

   ```bash
   pytest
   ruff check .
   mypy .
   ```

See `docs/usage` for workflow guides and `docs/ADRs` for architectural decisions.
