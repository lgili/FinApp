# Testing

Testing strategy and commands.

## Running tests

```bash
# Run all tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/
```

## Test types

- Unit tests: domain logic
- Integration tests: use cases + DB
- CLI tests: end-to-end command behavior

Aim for high coverage and fast unit tests.