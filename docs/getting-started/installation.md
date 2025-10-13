# Installation

Get Finlite running on your machine in just a few minutes.

---

## Prerequisites

Before installing Finlite, ensure you have:

- **Python 3.11 or higher** ([Download Python](https://www.python.org/downloads/))
- **Git** ([Download Git](https://git-scm.com/downloads))
- **pip** (comes with Python)

!!! tip "Check your Python version"
    ```bash
    python --version
    # Should show Python 3.11.x or higher
    ```

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/lgili/finapp.git
cd finapp/backend
```

### 2. Create Virtual Environment

=== "macOS/Linux"
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

=== "Windows"
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

=== "Windows (PowerShell)"
    ```powershell
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    ```

!!! success "Virtual environment activated"
    Your prompt should now show `(.venv)` at the beginning.

### 3. Install Finlite

```bash
pip install -e .
```

This installs Finlite in **editable mode** with all dependencies.

### 4. Initialize Database

```bash
fin init-db
```

This creates the SQLite database at `~/.finlite/finlite.db` (or location specified in `.env`).

### 5. Verify Installation

```bash
fin --version
fin --help
```

You should see the Finlite CLI help message with available commands.

---

## Configuration

Finlite uses environment variables for configuration. Create a `.env` file:

```bash title="backend/.env"
# Database location (default: ~/.finlite/finlite.db)
FINLITE_DATA_DIR=~/.finlite

# Default currency (default: USD)
DEFAULT_CURRENCY=USD

# Log level (default: INFO)
LOG_LEVEL=INFO
```

!!! info "Optional Configuration"
    The `.env` file is optional. Finlite works with sensible defaults.

---

## Development Installation

If you want to contribute or run tests:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run type checker
mypy backend/finlite

# Run linter
ruff check .

# Format code
ruff format .
```

---

## Troubleshooting

### Python Version Error

```
ERROR: This package requires Python 3.11 or higher
```

**Solution**: Install Python 3.11+ from [python.org](https://www.python.org/downloads/)

### Permission Denied

```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solution**: Use a virtual environment (recommended) or add `--user` flag:

```bash
pip install --user -e .
```

### Database Locked

```
sqlite3.OperationalError: database is locked
```

**Solution**: Close other Finlite instances and try again. SQLite doesn't support concurrent writes.

### Module Not Found

```
ModuleNotFoundError: No module named 'finlite'
```

**Solution**: Ensure you're in the virtual environment and installed with `-e .`:

```bash
source .venv/bin/activate  # Activate venv
pip install -e .            # Install package
```

---

## Updating Finlite

To update to the latest version:

```bash
cd finapp
git pull origin main
cd backend
pip install -e .  # Reinstall dependencies
```

---

## Uninstallation

To remove Finlite:

```bash
pip uninstall finlite
rm -rf ~/.finlite  # Remove database and config (optional)
```

---

## Next Steps

✅ Finlite is now installed!

Continue to:

- [Quick Start](quickstart.md) - Your first transactions in 5 minutes
- [First Steps](first-steps.md) - Learn the basics
- [CLI Reference](../user-guide/cli-reference.md) - Full command documentation
