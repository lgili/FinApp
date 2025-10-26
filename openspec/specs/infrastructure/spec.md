# Infrastructure

## Purpose
Capture persistence, logging, and adapter obligations so the application stack remains portable, observable, and aligned with local-first constraints.

## Requirements
### Requirement: SQLite Persistence with Unit of Work
The system MUST persist ledger data using SQLite with SQLAlchemy repositories coordinated through a unit of work pattern.

#### Scenario: Unit of work commits transaction
- **GIVEN** a `SqlAlchemyUnitOfWork` instance
- **WHEN** `uow.commit()` is called after saving a transaction
- **THEN** the transaction is flushed to SQLite
- **AND** the unit of work resets its session for reuse

### Requirement: Structured Logging
Infrastructure MUST emit structured logs using structlog with optional JSON output.

#### Scenario: JSON log mode
- **GIVEN** the CLI runs with `--json-logs`
- **WHEN** events occur (e.g., transaction recorded)
- **THEN** structlog emits JSON-formatted entries to stdout
- **AND** log metadata includes event name and identifiers
