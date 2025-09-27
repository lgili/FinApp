# Getting started with Finlite

This guide walks through initializing a fresh Finlite environment during Phase 0.

## Prerequisites

- Python 3.11+
- SQLite (bundled with Python on most systems)
- `uv` or `pip` for dependency management

## Setup steps

1. **Create a virtual environment**

   ```bash
   cd backend
   uv venv
   source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -e .[dev]
   ```

3. **Configure the data directory**

   ```bash
   cp ../.env.example ../.env
   # Edit FINLITE_DATA_DIR if you prefer a custom location
   ```

4. **Initialize the database**

   ```bash
   fin init-db
   ```

5. **Verify quality gates**

   ```bash
   pytest
   ruff check .
   mypy .
   ```

The CLI now exposes commands such as `fin accounts list` and `fin accounts add`.
