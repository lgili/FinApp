# Finlite

A production-ready, local-first personal finance toolkit implementing **Clean Architecture** with double-entry accounting, event-driven architecture, structured logging, and comprehensive CLI automation.

Built with Domain-Driven Design principles, SOLID patterns, and full test coverage (186 tests).

## ✨ Features

- 📊 **Double-Entry Accounting**: Proper balance validation and transaction recording
- 🏗️ **Clean Architecture**: Domain-driven design with clear layer separation
- 📡 **Event Bus**: Pub/sub pattern for audit logging and observability
- 📝 **Structured Logging**: Production-ready with JSON output and debug modes
- 🧪 **Full Test Coverage**: 186 tests (163 unit + 23 integration)
- 🎯 **Type Safety**: Complete type hints with mypy validation
- 🚀 **Rich CLI**: User-friendly terminal interface with colored output
- 💉 **Dependency Injection**: IoC container with dependency-injector

## 🏛️ Architecture

Finlite follows Clean Architecture with strict layer boundaries:

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

### Layer Details

**Domain Layer** (`backend/finlite/domain/`)
- Pure business logic, no external dependencies
- Entities: Account, Transaction, Posting
- Value Objects: AccountCode, AccountType, Money
- Domain Events: AccountCreated, TransactionRecorded
- Repository Interfaces: IAccountRepository, ITransactionRepository

**Application Layer** (`backend/finlite/application/`)
- Use Cases orchestrate business flows
- CreateAccountUseCase, RecordTransactionUseCase
- Publishes domain events for observability
- Emits structured logs for audit trails

**Infrastructure Layer** (`backend/finlite/infrastructure/`)
- SQLAlchemy ORM implementations
- InMemoryEventBus with pub/sub pattern
- Event handlers: AuditLogHandler, MetricsEventHandler
- Database session management with Unit of Work

**Interface Layer** (`backend/finlite/interfaces/`)
- Typer-based CLI with rich formatting
- Commands: accounts, transactions
- Global options: --debug, --json-logs
- Input validation and error handling

## 📡 Event-Driven Architecture

Finlite implements an event bus for decoupled observability:

```python
# Use cases publish domain events
event_bus.publish(AccountCreated(
    account_id=account.id,
    account_code=account.code,
    account_type=account.account_type
))

# Multiple handlers react independently
- AuditLogHandler: Records events for compliance
- ConsoleEventHandler: Prints events in dev mode
- MetricsEventHandler: Tracks event counts
```

**Benefits:**
- Audit trail for regulatory compliance
- Decoupled monitoring and alerting
- Easy to add new handlers without changing use cases
- Event sourcing preparation for future features

## 📝 Structured Logging

Production-ready logging with structlog:

```bash
# Human-readable development logs (colorized)
fin --debug accounts create -c "CASH" -n "Cash" -t ASSET
# 2025-10-12T14:30:00 [info] creating_account account_code=CASH

# JSON logs for production (log aggregation)
fin --json-logs accounts list
# {"event":"accounts_listed","level":"info","timestamp":"2025-10-12T14:30:00","count":5}
```

**Features:**
- Structured fields for easy querying
- ISO timestamps for log aggregation
- Exception tracebacks with context
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Context variables for request tracing

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/lgili/finapp.git
cd finapp/backend

# Create virtual environment (Python 3.11+)
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Create accounts
fin accounts create --code "CASH" --name "Cash" --type ASSET
fin accounts create --code "INCOME" --name "Salary" --type INCOME

# List accounts
fin accounts list

# Record transaction (interactive)
fin transactions create --description "Salary received"
# Posting 1 - Account: CASH, Amount: 5000
# Posting 2 - Account: INCOME, Amount: -5000

# Check balance
fin accounts balance CASH
# Balance: 5000.00 USD

# Enable debug logging
fin --debug transactions list --account CASH
```

See [CLI_GUIDE.md](CLI_GUIDE.md) for comprehensive examples.

## 📚 Documentation

- **[CLI Guide](CLI_GUIDE.md)**: Complete CLI usage with examples
- **[Migration Roadmap](MIGRATION_ROADMAP.md)**: Clean Architecture migration phases
- **[Project Plan](plan.md)**: Development roadmap and milestones
- **[Backend README](backend/README.md)**: Development setup

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=finlite --cov-report=term-missing

# Run specific test suites
pytest tests/unit/                    # Unit tests (163)
pytest tests/integration/             # CLI tests (23)
pytest tests/unit/domain/             # Domain layer
pytest tests/unit/infrastructure/     # Infrastructure layer
pytest tests/unit/application/        # Use cases

# Type checking
mypy backend/finlite

# Linting
ruff check backend/finlite
```

**Test Coverage:**
- ✅ 186 tests passing (163 unit + 23 integration)
- ✅ Domain entities and value objects
- ✅ Repository implementations
- ✅ Use cases with event publishing
- ✅ Event bus and handlers
- ✅ CLI commands and error handling

## 📂 Project Structure

```
finapp/
├── backend/
│   ├── finlite/
│   │   ├── domain/              # Business logic (entities, events)
│   │   │   ├── entities/        # Account, Transaction, Posting
│   │   │   ├── value_objects/   # Money, AccountCode, AccountType
│   │   │   ├── events/          # Domain events (AccountCreated, etc.)
│   │   │   └── repositories/    # Repository interfaces
│   │   ├── application/         # Use cases
│   │   │   └── use_cases/       # CreateAccount, RecordTransaction
│   │   ├── infrastructure/      # External services
│   │   │   ├── database/        # SQLAlchemy ORM, migrations
│   │   │   ├── events/          # Event bus, handlers
│   │   │   └── repositories/    # Repository implementations
│   │   ├── interfaces/          # User interfaces
│   │   │   └── cli/             # Typer CLI application
│   │   └── shared/              # Cross-cutting concerns
│   │       ├── di/              # Dependency injection container
│   │       └── observability/   # Structured logging
│   └── tests/
│       ├── unit/                # Unit tests (163)
│       │   ├── domain/          # Entity tests
│       │   ├── application/     # Use case tests
│       │   └── infrastructure/  # Repository, event bus tests
│       └── integration/         # CLI tests (23)
├── CLI_GUIDE.md                 # CLI usage guide
├── MIGRATION_ROADMAP.md         # Architecture migration phases
└── plan.md                      # Project roadmap
```

## 🔄 Development Workflow

```bash
# 1. Make changes
vim backend/finlite/domain/entities/account.py

# 2. Run tests
pytest tests/unit/domain/

# 3. Type check
mypy backend/finlite/domain/

# 4. Lint
ruff check backend/finlite/

# 5. Format
ruff format backend/finlite/

# 6. Test CLI
fin --debug accounts list
```

## 🎯 Design Patterns

Finlite implements several design patterns:

- **Repository Pattern**: Abstract data access
- **Unit of Work**: Transaction management
- **Dependency Injection**: IoC container for loose coupling
- **Observer Pattern**: Event bus for pub/sub
- **Value Object**: Immutable domain primitives
- **Factory Pattern**: Entity creation
- **Strategy Pattern**: Event handlers

## 🛠️ Technology Stack

- **Python 3.11+**: Modern Python with type hints
- **SQLAlchemy 2.0**: ORM with declarative mapping
- **Alembic**: Database migrations
- **Typer**: CLI framework with rich formatting
- **dependency-injector**: IoC container
- **structlog**: Structured logging
- **pytest**: Testing framework
- **mypy**: Static type checking
- **ruff**: Fast Python linter

## 📋 Roadmap

**Completed:**
- ✅ Phase 0-5: Legacy migration to Clean Architecture
- ✅ Phase 6: Event Bus & Domain Events
- ✅ Phase 7: Structured Logging & Documentation

**Future:**
- 🔲 Bank statement import
- 🔲 Rules engine for transaction classification
- 🔲 ML-assisted categorization
- 🔲 Investment tracking
- 🔲 Web API (FastAPI)
- 🔲 React frontend
- 🔲 Multi-currency support

See [MIGRATION_ROADMAP.md](MIGRATION_ROADMAP.md) for detailed phases.

## 🤝 Contributing

Contributions welcome! This project follows:

- Clean Architecture principles
- SOLID design patterns
- TDD with pytest
- Type hints with mypy
- Conventional Commits

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🔗 Links

- **GitHub**: [github.com/lgili/finapp](https://github.com/lgili/finapp)
- **Issues**: [github.com/lgili/finapp/issues](https://github.com/lgili/finapp/issues)
- **Documentation**: [CLI_GUIDE.md](CLI_GUIDE.md)
