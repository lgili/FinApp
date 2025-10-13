# Code Style

Finlite follows PEP8 and uses Ruff and Mypy for linting and static typing.

## Commands

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy backend/finlite
```

## Conventions
- Use type hints for public APIs
- Keep functions small and focused
- Add tests for new behavior
- Document public functions with docstrings