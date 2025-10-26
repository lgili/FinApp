<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Finlite** is a production-ready, local-first personal finance toolkit implementing Clean Architecture with double-entry accounting, event-driven architecture, structured logging, and comprehensive CLI automation.

The project is built with Python 3.11+ using Domain-Driven Design principles, SOLID patterns, and full test coverage (186 tests).

## Development Commands

### Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit/                    # Unit tests (163)
pytest tests/integration/             # Integration tests (23)
pytest tests/unit/domain/             # Domain layer only
pytest tests/unit/infrastructure/     # Infrastructure layer only
pytest tests/unit/application/        # Application/use cases only

# Run with coverage
pytest --cov=finlite --cov-report=term-missing

# Run a single test file
pytest tests/unit/domain/test_account.py

# Run a single test function
pytest tests/unit/domain/test_account.py::test_account_creation
```

### Code Quality
```bash
# Type checking
mypy backend/finlite

# Linting
ruff check backend/finlite

# Formatting
ruff format backend/finlite

# All quality checks (CI)
cd backend && make ci
# Or manually: ruff check . && ruff format --check . && mypy . && pytest
```

### Running the CLI
```bash
# Global options
fin --debug              # Enable debug logging
fin --json-logs          # JSON output for log aggregation
fin --version            # Show version
fin --help               # Show help

# Account commands
fin accounts create -c "CASH" -n "Cash" -t ASSET
fin accounts list
fin accounts balance CASH

# Transaction commands
fin transactions create -d "Description"
fin transactions list
fin transactions list --account CASH --limit 10
```

### Database
```bash
# Initialize database
fin init-db

# Run migrations
cd backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# View migration history
alembic history
```

## Architecture

Finlite follows **Clean Architecture** with strict layer boundaries:

```
┌─────────────────────────────────────────────────────────────┐
│                     🖥️  Interface Layer                      │
│                    (CLI, API, Adapters)                      │
├─────────────────────────────────────────────────────────────┤
│                   📋 Application Layer                       │
│              (Use Cases, Business Logic)                     │
├─────────────────────────────────────────────────────────────┤
│                     💎 Domain Layer                          │
│           (Entities, Value Objects, Events)                  │
├─────────────────────────────────────────────────────────────┤
│                  🔧 Infrastructure Layer                      │
│         (Database, Event Bus, External Services)             │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Domain Layer** (`backend/finlite/domain/`)
- Pure business logic with no external dependencies
- Entities: `Account`, `Transaction`, `Posting`, `ImportBatch`, `StatementEntry`
- Value Objects: `Money`, `AccountType`, `AccountCode`
- Domain Events: `AccountCreated`, `TransactionRecorded`
- Repository Interfaces (ABC): `IAccountRepository`, `ITransactionRepository`
- Domain exceptions: `UnbalancedTransactionError`, `AccountNotFoundError`, etc.

**Application Layer** (`backend/finlite/application/`)
- Use cases orchestrate business flows
- Publishes domain events for observability
- Emits structured logs for audit trails
- Use cases: `CreateAccountUseCase`, `RecordTransactionUseCase`, `ImportNubankUseCase`
- DTOs for input/output

**Infrastructure Layer** (`backend/finlite/infrastructure/`)
- SQLAlchemy ORM implementations with UUID-Integer conversion layer
- `InMemoryEventBus` with pub/sub pattern
- Event handlers: `AuditLogHandler`, `MetricsEventHandler`
- Database session management with Unit of Work pattern
- Structured logging with `structlog`

**Interface Layer** (`backend/finlite/interfaces/`)
- Typer-based CLI with rich formatting
- Commands: `accounts`, `transactions`
- Global options: `--debug`, `--json-logs`
- Input validation and error handling

### Key Design Patterns

- **Repository Pattern**: Abstract data access
- **Unit of Work**: Transaction management
- **Dependency Injection**: IoC container (`shared/di/container.py`) for loose coupling
- **Observer Pattern**: Event bus for pub/sub
- **Value Object**: Immutable domain primitives
- **Factory Pattern**: Entity creation
- **UUID-Integer Conversion**: Domain uses UUIDs, database uses integers for performance

## Project Structure

```
backend/
├── finlite/
│   ├── domain/              # Business logic (entities, value objects, events)
│   │   ├── entities/        # Account, Transaction, Posting, ImportBatch
│   │   ├── value_objects/   # Money, AccountCode, AccountType
│   │   ├── events/          # Domain events
│   │   └── repositories/    # Repository interfaces (ABC)
│   ├── application/         # Use cases and DTOs
│   │   ├── use_cases/       # CreateAccount, RecordTransaction, etc.
│   │   └── dtos/            # Data transfer objects
│   ├── infrastructure/      # External services
│   │   ├── persistence/     # SQLAlchemy repositories, models, mappers
│   │   ├── events/          # Event bus and handlers
│   │   └── observability/   # Structured logging
│   ├── interfaces/          # User interfaces
│   │   └── cli/             # Typer CLI application
│   └── shared/              # Cross-cutting concerns
│       ├── di/              # Dependency injection container
│       └── observability/   # Logging setup
├── tests/
│   ├── unit/                # Fast tests without DB (163 tests)
│   │   ├── domain/          # Entity tests
│   │   ├── application/     # Use case tests with mocks
│   │   └── infrastructure/  # Repository tests
│   └── integration/         # Tests with DB (23 tests)
└── alembic/                 # Database migrations
```

## Important Implementation Details

### UUID-Integer Conversion Layer
The domain layer uses UUIDs for entity IDs, but the database uses integers for performance. The infrastructure layer handles conversion:
- Domain entities have UUID IDs
- SQLAlchemy models have integer IDs
- Mappers convert between UUID and integer using a conversion table
- Repository implementations handle this transparently

### Event-Driven Architecture
The event bus enables decoupled observability:
- Use cases publish domain events (`AccountCreated`, `TransactionRecorded`)
- Multiple handlers react independently (audit logging, metrics, console output)
- New handlers can be added without changing use cases

### Double-Entry Accounting Rules
- Every transaction must have at least 2 postings
- Sum of all posting amounts must equal zero
- Account types: ASSET, LIABILITY, EQUITY, INCOME, EXPENSE
- Posting amounts: positive for debit, negative for credit

### Structured Logging
Production-ready logging with `structlog`:
- Human-readable development logs (colorized) with `--debug`
- JSON logs for production/log aggregation with `--json-logs`
- Structured fields for easy querying
- ISO timestamps for log aggregation
- Exception tracebacks with context

## Testing Strategy

The project follows a test pyramid approach:

1. **Unit Tests (Domain)** - Fast, no I/O, pure business logic
   - Test entities, value objects, domain rules
   - No database, no external dependencies
   - Example: `tests/unit/domain/test_account.py`

2. **Unit Tests (Application)** - Mock repositories
   - Test use cases with mocked dependencies
   - Example: `tests/unit/application/test_create_account.py`

3. **Integration Tests** - Real database (in-memory SQLite)
   - Test repository implementations
   - Test database round-trips
   - Example: `tests/integration/test_account_repository.py`

4. **E2E Tests** - Full CLI workflows
   - Test complete user scenarios
   - Example: Import → Rules → Post → Report

When writing tests:
- Use `pytest` markers: `@pytest.mark.unit`, `@pytest.mark.integration`
- Mock external dependencies in unit tests
- Use fixtures for common test data
- Follow AAA pattern: Arrange, Act, Assert
- Test error cases and edge conditions

## Migration Status

The project is in active migration to Clean Architecture. See `MIGRATION_ROADMAP.md` for details.

**Completed Phases:**
- ✅ Phase 0-5: Core accounting, Clean Architecture migration
- ✅ Phase 6: Event Bus & Domain Events
- ✅ Phase 7: Structured Logging & Documentation

**Active Development:**
- Domain Layer: 100% complete with 82 tests
- Infrastructure: Repository pattern implemented with UUID-Integer conversion
- Application: Use cases for accounts and transactions
- CLI: Refactored as thin adapters over use cases

## Configuration

Configuration is managed via Pydantic Settings (`backend/finlite/config.py`):
- Database URL: `DATABASE_URL` environment variable
- Default: SQLite at `~/.finlite/finlite.db`
- Supports environment-specific configs

## Common Workflows

### Adding a New Entity
1. Create entity in `domain/entities/`
2. Create repository interface in `domain/repositories/`
3. Create SQLAlchemy model in `infrastructure/persistence/sqlalchemy/models.py`
4. Implement repository in `infrastructure/persistence/sqlalchemy/repositories/`
5. Create mapper in `infrastructure/persistence/sqlalchemy/mappers/`
6. Write unit tests in `tests/unit/domain/`
7. Write integration tests in `tests/integration/`

### Adding a New Use Case
1. Create use case in `application/use_cases/`
2. Define DTOs in `application/dtos/`
3. Wire dependencies in `shared/di/container.py`
4. Create CLI command in `interfaces/cli/commands/`
5. Write unit tests with mocked repositories
6. Add to main CLI app

### Adding a New CLI Command
1. Create command in `interfaces/cli/commands/`
2. Keep it thin - delegate to use cases
3. Use Rich for output formatting
4. Handle errors gracefully
5. Add help text and examples
6. Test with E2E tests

## Commit Message Convention

Follow Conventional Commits:
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring
- `test:` Adding tests
- `docs:` Documentation changes
- `chore:` Build/tooling changes

Example: `feat(domain): add Account entity with validation`
