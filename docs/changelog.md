# Changelog

All notable changes to Finlite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Bank statement import (Nubank, OFX)
- Rules engine for auto-classification
- ML-assisted transaction categorization
- Financial reports (Balance Sheet, Income Statement)
- Investment portfolio tracking
- Terminal UI (TUI)

---

## [0.1.0] - 2025-10-12

### 🎉 Initial Release

First production-ready release of Finlite with complete Clean Architecture implementation.

### ✨ Added

**Core Accounting**
- Double-entry bookkeeping system
- Five account types: Asset, Liability, Equity, Income, Expense
- Multi-currency support (USD, BRL, EUR, etc.)
- Transaction recording with automatic balance validation
- Account balance calculation
- Transaction history with filtering

**Architecture**
- Clean Architecture with four layers (Domain, Application, Infrastructure, Interface)
- Domain entities: Account, Transaction, Posting
- Repository pattern with SQLAlchemy
- Dependency injection with DI container
- Type-safe codebase with 100% mypy coverage

**Event-Driven Architecture**
- Event bus with publish/subscribe pattern
- Domain events: AccountCreated, TransactionRecorded, etc.
- Event handlers: AuditLogHandler, ConsoleEventHandler, MetricsEventHandler
- Complete audit trail for compliance

**Observability**
- Structured logging with structlog
- JSON output for production log aggregation
- Colorized console output for development
- Debug mode with `--debug` flag
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

**CLI Interface**
- `fin accounts create` - Create new accounts
- `fin accounts list` - List all accounts with filtering
- `fin accounts balance` - Get account balance
- `fin transactions create` - Record transactions (interactive)
- `fin transactions list` - View transaction history with filtering
- `fin init-db` - Initialize database
- Global options: `--debug`, `--json-logs`, `--version`, `--help`

**Documentation**
- Professional MkDocs documentation with Material theme
- Comprehensive guides: Installation, Quick Start, CLI Reference
- Architecture documentation with Mermaid diagrams
- Double-entry accounting tutorial
- Contributing guidelines
- Automated GitHub Pages deployment

**Testing & Quality**
- 187 tests (163 unit + 24 integration)
- pytest for testing framework
- ruff for linting and formatting
- mypy for type checking
- Pre-commit hooks for code quality
- CI/CD with GitHub Actions

### 📊 Metrics
- Lines of Code: ~8,000
- Test Coverage: 187 tests passing
- Type Coverage: 100%
- Documentation Pages: 12+

---

## [0.0.1] - 2025-09-15

### 🏗️ Foundation

**Infrastructure**
- Initial project structure
- Python packaging with pyproject.toml
- SQLite database with Alembic migrations
- Development environment setup

**Tooling**
- pytest configuration
- ruff configuration
- mypy strict mode
- Git repository with .gitignore

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| [0.1.0] | 2025-10-12 | Initial production release |
| [0.0.1] | 2025-09-15 | Project foundation |

---

## Upgrade Guide

### From 0.0.1 to 0.1.0

This is a major architectural change. Follow these steps:

1. **Backup your data**:
```bash
cp ~/.finlite/finlite.db ~/.finlite/finlite.db.backup
```

2. **Update code**:
```bash
cd finapp
git pull origin main
cd backend
pip install -e .
```

3. **Run migrations** (if needed):
```bash
fin init-db
```

4. **Test your data**:
```bash
fin accounts list
fin transactions list --limit 10
```

---

## Migration Notes

### Database Schema Changes

**v0.1.0**:
- Added `events` table for audit logging
- Added `is_active` column to accounts
- Added `parent_id` for hierarchical accounts
- Added indexes for performance

---

## Breaking Changes

### v0.1.0

No breaking changes from 0.0.1 (data is compatible).

---

## Deprecations

None yet.

---

## Security

### v0.1.0

- SQLite with WAL mode for data integrity
- Parameterized queries to prevent SQL injection
- No external network access (local-first)
- No user credentials stored

---

## Performance Improvements

### v0.1.0

- Efficient balance calculation with indexed queries
- Batch event handling
- Lazy loading of relationships
- Sub-second query times for 10k+ transactions

---

## Bug Fixes

### v0.1.0

- Fixed transaction balance validation edge cases
- Fixed date parsing in different locales
- Fixed CLI output encoding issues
- Fixed event handler error propagation

---

## Known Issues

### v0.1.0

- [ ] No undo/rollback for transactions (planned for v0.2.0)
- [ ] Limited to single currency per account (multi-currency accounts in v0.3.0)
- [ ] No bulk import yet (coming in v0.2.0)
- [ ] CLI-only interface (TUI in v0.4.0, Web UI in v0.5.0)

---

## Contributors

Thank you to all contributors who made this release possible!

- [@lgili](https://github.com/lgili) - Project lead and primary developer

Want to contribute? Check our [Contributing Guide](development/contributing.md)!

---

## Links

- [Documentation](https://lgili.github.io/finapp/)
- [GitHub Repository](https://github.com/lgili/finapp)
- [Issue Tracker](https://github.com/lgili/finapp/issues)
- [Roadmap](roadmap.md)

---

*For older changes, see [GitHub Releases](https://github.com/lgili/finapp/releases).*
