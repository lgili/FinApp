# Quality

## Purpose
Set the minimum automated testing, linting, and regression safeguards required to keep Finlite reliable as the codebase evolves.

## Requirements
### Requirement: Automated Test Coverage
The project MUST maintain automated tests for domain, application, infrastructure, and CLI layers with continuous integration checks.

#### Scenario: Pytest suite enforces coverage
- **GIVEN** the developer runs `pytest -ra --strict-markers --cov`
- **WHEN** the suite completes
- **THEN** all domain/application/integration tests pass
- **AND** coverage results are reported in CI

### Requirement: Static Analysis Gates
All code changes MUST pass Ruff linting/formatting and mypy strict type checking before merge.

#### Scenario: Pre-commit enforces lint and types
- **GIVEN** a developer commits changes
- **WHEN** pre-commit hooks execute
- **THEN** `ruff check`, `ruff format`, and `mypy --strict` run successfully
- **AND** the commit is rejected if any tool fails
