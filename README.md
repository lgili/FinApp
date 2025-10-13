<div align="center"># Finlite



# FinliteA production-ready, local-first personal finance toolkit implementing **Clean Architecture** with double-entry accounting, event-driven architecture, structured logging, and comprehensive CLI automation.



**Local-first personal finance toolkit with double-entry accounting**Built with Domain-Driven Design principles, SOLID patterns, and full test coverage (186 tests).



[![Tests](https://img.shields.io/badge/tests-187%20passing-success)](https://github.com/lgili/finapp/actions)## ✨ Features

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)

[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)- 📊 **Double-Entry Accounting**: Proper balance validation and transaction recording

[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](http://mypy-lang.org/)- 🏗️ **Clean Architecture**: Domain-driven design with clear layer separation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)- 📡 **Event Bus**: Pub/sub pattern for audit logging and observability

- 📝 **Structured Logging**: Production-ready with JSON output and debug modes

[Documentation](https://lgili.github.io/finapp/) • - 🧪 **Full Test Coverage**: 186 tests (163 unit + 23 integration)

[Quick Start](#quick-start) • - 🎯 **Type Safety**: Complete type hints with mypy validation

[Features](#features) • - 🚀 **Rich CLI**: User-friendly terminal interface with colored output

[Architecture](#architecture) • - 💉 **Dependency Injection**: IoC container with dependency-injector

[Contributing](#contributing)

## 🏛️ Architecture

</div>

Finlite follows Clean Architecture with strict layer boundaries:

---

```

## Overview┌─────────────────────────────────────────────────────────────┐

│                     🖥️  Interface Layer                      │

Finlite is a **modern, local-first personal finance application** built with **Clean Architecture** principles and **double-entry bookkeeping**. It provides a powerful CLI for managing your finances with the precision of professional accounting software, while keeping your data completely private on your machine.│                    (CLI, API, Adapters)                      │

├─────────────────────────────────────────────────────────────┤

### Why Finlite?│                   📋 Application Layer                       │

│              (Use Cases, Business Logic)                     │

- 🔒 **Privacy First**: Your financial data never leaves your machine├─────────────────────────────────────────────────────────────┤

- 💎 **Rock-Solid Accounting**: Double-entry bookkeeping catches errors automatically│                     💎 Domain Layer                          │

- 🏗️ **Clean Architecture**: Maintainable, testable, and extensible codebase│           (Entities, Value Objects, Events)                  │

- 📊 **Multi-Currency**: Support for USD, BRL, EUR, and more├─────────────────────────────────────────────────────────────┤

- 🧪 **Well-Tested**: 187 tests (163 unit + 24 integration)│                  🔧 Infrastructure Layer                      │

- 🎯 **Type-Safe**: Full mypy type checking│         (Database, Event Bus, External Services)             │

- 📝 **Event-Driven**: Complete audit trail with domain events└─────────────────────────────────────────────────────────────┘

- 🔍 **Observable**: Structured logging with JSON output```



---### Layer Details



## Features**Domain Layer** (`backend/finlite/domain/`)

- Pure business logic, no external dependencies

### Core Accounting- Entities: Account, Transaction, Posting

- Value Objects: AccountCode, AccountType, Money

✅ **Double-Entry Bookkeeping** - Every transaction balances to zero  - Domain Events: AccountCreated, TransactionRecorded

✅ **Five Account Types** - Assets, Liabilities, Equity, Income, Expenses  - Repository Interfaces: IAccountRepository, ITransactionRepository

✅ **Multi-Currency Support** - Handle multiple currencies seamlessly  

✅ **Transaction History** - Complete ledger with filtering and search  **Application Layer** (`backend/finlite/application/`)

✅ **Account Balances** - Real-time balance calculations  - Use Cases orchestrate business flows

- CreateAccountUseCase, RecordTransactionUseCase

### Developer Experience- Publishes domain events for observability

- Emits structured logs for audit trails

✅ **Clean Architecture** - SOLID principles, clear separation of concerns  

✅ **Type Safety** - 100% type-checked with mypy  **Infrastructure Layer** (`backend/finlite/infrastructure/`)

✅ **Dependency Injection** - Testable and flexible design  - SQLAlchemy ORM implementations

✅ **Event Bus** - Domain events for audit trails and observability  - InMemoryEventBus with pub/sub pattern

✅ **Structured Logging** - Production-ready logging with structlog  - Event handlers: AuditLogHandler, MetricsEventHandler

- Database session management with Unit of Work

### CLI Features

**Interface Layer** (`backend/finlite/interfaces/`)

✅ **Intuitive Commands** - Natural command-line interface with Typer  - Typer-based CLI with rich formatting

✅ **Debug Mode** - Detailed logging with `--debug` flag  - Commands: accounts, transactions

✅ **JSON Logs** - Machine-readable output with `--json-logs`  - Global options: --debug, --json-logs

✅ **Rich Output** - Beautiful tables and formatting  - Input validation and error handling



---## 📡 Event-Driven Architecture



## Quick StartFinlite implements an event bus for decoupled observability:



### Installation```python

# Use cases publish domain events

```bashevent_bus.publish(AccountCreated(

# Clone the repository    account_id=account.id,

git clone https://github.com/lgili/finapp.git    account_code=account.code,

cd finapp/backend    account_type=account.account_type

))

# Create virtual environment

python -m venv .venv# Multiple handlers react independently

source .venv/bin/activate  # Windows: .venv\Scripts\activate- AuditLogHandler: Records events for compliance

- ConsoleEventHandler: Prints events in dev mode

# Install package- MetricsEventHandler: Tracks event counts

pip install -e .```



# Initialize database**Benefits:**

fin init-db- Audit trail for regulatory compliance

```- Decoupled monitoring and alerting

- Easy to add new handlers without changing use cases

### Your First Transaction- Event sourcing preparation for future features



```bash## 📝 Structured Logging

# Create accounts

fin accounts create --code "CASH" --name "Cash" --type ASSETProduction-ready logging with structlog:

fin accounts create --code "EQUITY" --name "Opening Balance" --type EQUITY

```bash

# Record opening balance# Human-readable development logs (colorized)

fin transactions create --description "Opening balance"fin --debug accounts create -c "CASH" -n "Cash" -t ASSET

# Posting 1: CASH, 1000# 2025-10-12T14:30:00 [info] creating_account account_code=CASH

# Posting 2: EQUITY, -1000

# JSON logs for production (log aggregation)

# Check balancefin --json-logs accounts list

fin accounts balance CASH# {"event":"accounts_listed","level":"info","timestamp":"2025-10-12T14:30:00","count":5}

# Balance: 1000.00 USD```

```

**Features:**

📚 **[Full Quick Start Guide →](https://lgili.github.io/finapp/getting-started/quickstart/)**- Structured fields for easy querying

- ISO timestamps for log aggregation

---- Exception tracebacks with context

- Configurable log levels (DEBUG, INFO, WARNING, ERROR)

## Architecture- Context variables for request tracing



Finlite follows **Clean Architecture** with clear separation of concerns:## 🚀 Quick Start



```### Installation

┌─────────────────────────────────────────────────────┐

│                  Interface Layer                    │```bash

│                   (CLI - Typer)                     │# Clone repository

└──────────────────────┬──────────────────────────────┘git clone https://github.com/lgili/finapp.git

                       │cd finapp/backend

┌──────────────────────▼──────────────────────────────┐

│                Application Layer                    │# Create virtual environment (Python 3.11+)

│         (Use Cases, Business Operations)            │python -m venv venv

└──────────────────────┬──────────────────────────────┘source venv/bin/activate  # or `venv\Scripts\activate` on Windows

                       │

┌──────────────────────▼──────────────────────────────┐# Install with dev dependencies

│                  Domain Layer                       │pip install -e ".[dev]"

│    (Entities, Value Objects, Domain Events)         │```

└──────────────────────▲──────────────────────────────┘

                       │### Basic Usage

┌──────────────────────┴──────────────────────────────┐

│              Infrastructure Layer                   │```bash

│    (Database, Event Bus, Logging, External APIs)    │# Create accounts

└─────────────────────────────────────────────────────┘fin accounts create --code "CASH" --name "Cash" --type ASSET

```fin accounts create --code "INCOME" --name "Salary" --type INCOME



### Key Design Patterns# List accounts

fin accounts list

- **Repository Pattern**: Abstract data access

- **Dependency Injection**: Loose coupling and testability# Record transaction (interactive)

- **Event-Driven**: Domain events for observabilityfin transactions create --description "Salary received"

- **Factory Pattern**: Clean object creation# Posting 1 - Account: CASH, Amount: 5000

- **Command Pattern**: CLI commands as objects# Posting 2 - Account: INCOME, Amount: -5000



📐 **[Full Architecture Documentation →](https://lgili.github.io/finapp/architecture/overview/)**# Check balance

fin accounts balance CASH

---# Balance: 5000.00 USD



## Project Structure# Enable debug logging

fin --debug transactions list --account CASH

``````

finapp/

├── backend/See [CLI_GUIDE.md](CLI_GUIDE.md) for comprehensive examples.

│   ├── finlite/

│   │   ├── domain/              # 💎 Business logic (entities, events)## 📚 Documentation

│   │   ├── application/         # ⚙️ Use cases and orchestration

│   │   ├── infrastructure/      # 🔧 Database, event bus, external- **[CLI Guide](CLI_GUIDE.md)**: Complete CLI usage with examples

│   │   ├── interfaces/          # 🖥️ CLI and future APIs- **[Migration Roadmap](MIGRATION_ROADMAP.md)**: Clean Architecture migration phases

│   │   └── shared/              # 🔗 DI container, logging, utilities- **[Project Plan](plan.md)**: Development roadmap and milestones

│   ├── tests/                   # 🧪 All tests (unit + integration)- **[Backend README](backend/README.md)**: Development setup

│   └── pyproject.toml           # Dependencies and project config

│## 🧪 Testing

├── docs/                        # 📖 MkDocs documentation

├── CLI_GUIDE.md                 # 📋 Comprehensive CLI reference```bash

└── README.md                    # 👋 This file# Run all tests

```pytest



---# Run with coverage

pytest --cov=finlite --cov-report=term-missing

## Usage Examples

# Run specific test suites

### Account Managementpytest tests/unit/                    # Unit tests (163)

pytest tests/integration/             # CLI tests (23)

```bashpytest tests/unit/domain/             # Domain layer

# Create accountspytest tests/unit/infrastructure/     # Infrastructure layer

fin accounts create -c "CHECKING" -n "Checking Account" -t ASSETpytest tests/unit/application/        # Use cases

fin accounts create -c "SALARY" -n "Salary" -t INCOME

fin accounts create -c "GROCERIES" -n "Groceries" -t EXPENSE# Type checking

mypy backend/finlite

# List accounts

fin accounts list# Linting

ruff check backend/finlite

# Get balance```

fin accounts balance CHECKING

```**Test Coverage:**

- ✅ 186 tests passing (163 unit + 23 integration)

### Recording Transactions- ✅ Domain entities and value objects

- ✅ Repository implementations

```bash- ✅ Use cases with event publishing

# Receive salary- ✅ Event bus and handlers

fin transactions create -d "Monthly salary"- ✅ CLI commands and error handling

# CHECKING: +3000, SALARY: -3000

## 📂 Project Structure

# Pay for groceries

fin transactions create -d "Weekly groceries"```

# GROCERIES: +150, CHECKING: -150finapp/

├── backend/

# View history│   ├── finlite/

fin transactions list --account CHECKING --limit 10│   │   ├── domain/              # Business logic (entities, events)

```│   │   │   ├── entities/        # Account, Transaction, Posting

│   │   │   ├── value_objects/   # Money, AccountCode, AccountType

### Debug and Logging│   │   │   ├── events/          # Domain events (AccountCreated, etc.)

│   │   │   └── repositories/    # Repository interfaces

```bash│   │   ├── application/         # Use cases

# Enable debug logging│   │   │   └── use_cases/       # CreateAccount, RecordTransaction

fin --debug accounts create -c "TEST" -n "Test" -t ASSET│   │   ├── infrastructure/      # External services

│   │   │   ├── database/        # SQLAlchemy ORM, migrations

# JSON output for log aggregation│   │   │   ├── events/          # Event bus, handlers

fin --json-logs transactions list│   │   │   └── repositories/    # Repository implementations

```│   │   ├── interfaces/          # User interfaces

│   │   │   └── cli/             # Typer CLI application

🎯 **[Full CLI Reference →](https://lgili.github.io/finapp/user-guide/cli-reference/)**│   │   └── shared/              # Cross-cutting concerns

│   │       ├── di/              # Dependency injection container

---│   │       └── observability/   # Structured logging

│   └── tests/

## Development│       ├── unit/                # Unit tests (163)

│       │   ├── domain/          # Entity tests

### Prerequisites│       │   ├── application/     # Use case tests

│       │   └── infrastructure/  # Repository, event bus tests

- Python 3.11+│       └── integration/         # CLI tests (23)

- Git├── CLI_GUIDE.md                 # CLI usage guide

- pip├── MIGRATION_ROADMAP.md         # Architecture migration phases

└── plan.md                      # Project roadmap

### Setup Development Environment```



```bash## 🔄 Development Workflow

cd backend

```bash

# Install with dev dependencies# 1. Make changes

pip install -e ".[dev]"vim backend/finlite/domain/entities/account.py



# Run tests# 2. Run tests

pytest tests/pytest tests/unit/domain/



# Type checking# 3. Type check

mypy finlitemypy backend/finlite/domain/



# Linting# 4. Lint

ruff check .ruff check backend/finlite/



# Format code# 5. Format

ruff format .ruff format backend/finlite/

```

# 6. Test CLI

### Running Testsfin --debug accounts list

```

```bash

# All tests## 🎯 Design Patterns

pytest tests/ -v

Finlite implements several design patterns:

# Unit tests only

pytest tests/unit/- **Repository Pattern**: Abstract data access

- **Unit of Work**: Transaction management

# Integration tests only- **Dependency Injection**: IoC container for loose coupling

pytest tests/integration/- **Observer Pattern**: Event bus for pub/sub

- **Value Object**: Immutable domain primitives

# With coverage- **Factory Pattern**: Entity creation

pytest tests/ --cov=finlite --cov-report=html- **Strategy Pattern**: Event handlers

```

## 🛠️ Technology Stack

### Project Quality

- **Python 3.11+**: Modern Python with type hints

- ✅ **187 tests** (163 unit + 24 integration)- **SQLAlchemy 2.0**: ORM with declarative mapping

- ✅ **100% type coverage** with mypy- **Alembic**: Database migrations

- ✅ **Ruff** for linting and formatting- **Typer**: CLI framework with rich formatting

- ✅ **Pre-commit hooks** for code quality- **dependency-injector**: IoC container

- ✅ **Clean Architecture** principles- **structlog**: Structured logging

- ✅ **SOLID** design patterns- **pytest**: Testing framework

- **mypy**: Static type checking

🛠️ **[Contributing Guide →](https://lgili.github.io/finapp/development/contributing/)**- **ruff**: Fast Python linter



---## 📋 Roadmap



## Roadmap**Completed:**

- ✅ Phase 0-5: Legacy migration to Clean Architecture

- [x] **Phase 0-5**: Core accounting, Clean Architecture migration- ✅ Phase 6: Event Bus & Domain Events

- [x] **Phase 6**: Event Bus & Domain Events  - ✅ Phase 7: Structured Logging & Documentation

- [x] **Phase 7**: Structured Logging & Documentation

- [ ] **Phase 8**: Bank statement import (Nubank, OFX)**Future:**

- [ ] **Phase 9**: Rules engine for auto-classification- 🔲 Bank statement import

- [ ] **Phase 10**: Reports (Balance Sheet, Income Statement)- 🔲 Rules engine for transaction classification

- [ ] **Phase 11**: Investment tracking (PM médio, P/L)- 🔲 ML-assisted categorization

- [ ] **Phase 12**: TUI (Terminal UI) with Textual- 🔲 Investment tracking

- [ ] **Phase 13**: Natural language CLI with Pydantic AI- 🔲 Web API (FastAPI)

- 🔲 React frontend

📅 **[Full Roadmap →](https://lgili.github.io/finapp/roadmap/)**- 🔲 Multi-currency support



---See [MIGRATION_ROADMAP.md](MIGRATION_ROADMAP.md) for detailed phases.



## Contributing## 🤝 Contributing



We welcome contributions! Whether it's:Contributions welcome! This project follows:



- 🐛 Bug reports- Clean Architecture principles

- 💡 Feature requests- SOLID design patterns

- 📖 Documentation improvements- TDD with pytest

- 🔧 Code contributions- Type hints with mypy

- Conventional Commits

**Ways to contribute**:

## 📄 License

1. 🍴 Fork the repository

2. 🌿 Create a feature branch (`git checkout -b feature/amazing-feature`)MIT License - see [LICENSE](LICENSE) file

3. ✅ Write tests for your changes

4. 📝 Commit with clear messages (`git commit -m 'feat: add amazing feature'`)## 🔗 Links

5. 📤 Push to your branch (`git push origin feature/amazing-feature`)

6. 🎉 Open a Pull Request- **GitHub**: [github.com/lgili/finapp](https://github.com/lgili/finapp)

- **Issues**: [github.com/lgili/finapp/issues](https://github.com/lgili/finapp/issues)

📋 **[Contributing Guidelines →](https://lgili.github.io/finapp/development/contributing/)**- **Documentation**: [CLI_GUIDE.md](CLI_GUIDE.md)


---

## License

Finlite is open-source software licensed under the **[MIT License](LICENSE)**.

---

## Documentation

📚 **[Full Documentation](https://lgili.github.io/finapp/)** - Complete guides and API reference

**Quick Links**:

- [Installation](https://lgili.github.io/finapp/getting-started/installation/)
- [Quick Start](https://lgili.github.io/finapp/getting-started/quickstart/)
- [CLI Reference](https://lgili.github.io/finapp/user-guide/cli-reference/)
- [Architecture](https://lgili.github.io/finapp/architecture/overview/)
- [Double-Entry Guide](https://lgili.github.io/finapp/user-guide/double-entry/)

---

## Support

Need help?

- 📖 [Documentation](https://lgili.github.io/finapp/)
- 🐛 [Issue Tracker](https://github.com/lgili/finapp/issues)
- 💬 [Discussions](https://github.com/lgili/finapp/discussions)

---

<div align="center">

**Built with ❤️ for financial clarity**

⭐ Star us on GitHub if you find Finlite useful!

[Documentation](https://lgili.github.io/finapp/) • 
[GitHub](https://github.com/lgili/finapp) • 
[Issues](https://github.com/lgili/finapp/issues) • 
[Discussions](https://github.com/lgili/finapp/discussions)

</div>
