# Finlite

Finlite is a local-first personal finance toolkit with double-entry accounting, rich CLI automation, and a roadmap towards rules, ML-assisted classification, and investment tracking.

This repository follows the roadmap captured in `plan.md`. Phase 0 provides the foundational tooling: project structure, database migrations, CLI entry point, and quality gates.

## Repository layout

```
finlite/
  backend/      # Python package + CLI (`fin`)
  docs/         # ADRs, usage guides
  examples/     # Sample datasets (placeholders for now)
```

## Quick start

See `docs/usage/getting-started.md` for detailed instructions. The abridged workflow:

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies with `pip install -e .[dev]` inside `backend/`.
3. Copy `.env.example` to `.env` and adjust `FINLITE_DATA_DIR` if desired.
4. Run `fin init-db` to apply migrations and seed the chart of accounts.
5. Check quality gates: `pytest`, `ruff check .`, `mypy .`.

## CLI preview

```
$ fin --help
Usage: fin [OPTIONS] COMMAND [ARGS]...

  Finlite CLI — local-first double-entry accounting

Options:
  --help  Show this message and exit.

Commands:
  accounts  Account management commands
  config    Display effective configuration values
  export    Export data to external formats
  init-db   Create the SQLite database and apply migrations
  report    Reporting commands
  txn       Transaction commands
```

## Next steps

- Phase 1: Manual transaction entry CLI and cashflow reporting
- Phase 2: Bank statement ingestion and rules engine
- Phase 3: ML-assisted classification

Contributions welcome—see `docs/ADRs/ADR-0001.md` for architectural context.
