# Project Context

## Purpose
Finlite is a local-first personal finance toolkit that applies clean architecture and double-entry accounting principles to keep personal ledgers accurate, auditable, and private. The goal is to provide a production-grade CLI for tracking accounts, transactions, and imports while preserving strong domain invariants and extensibility.

## Tech Stack
- Python 3.11+
- Typer CLI with Rich presenters for terminal UX
- SQLAlchemy ORM over SQLite (default) with Alembic migrations
- dependency-injector for IoC/container management
- Pydantic v2 + pydantic-settings for configuration
- structlog for structured logging and observability
- Pytest, pytest-cov, mypy (strict), Ruff (lint + formatting) for quality gates

## Project Conventions

### Code Style
- PEP 8 aligned with Ruff enforcing lint rules (line length 100, strict categories)
- Ruff format as the canonical code formatter; keep imports sorted automatically
- Strict typing with mypy (`--strict`) and exhaustive type hints on public APIs
- Prefer descriptive, domain-led naming (AccountRepository, ImportBatch, etc.) across layers

### Architecture Patterns
- Clean/hexagonal architecture with strict layer boundaries (Interfaces → Application → Domain → Infrastructure)
- Domain-driven design with rich domain entities, value objects, and domain events
- Event-driven auditing via internal event bus and structured logging for observability
- Dependency inversion everywhere: interfaces/ports in domain, adapters in infrastructure

### Testing Strategy
- Pytest with strict markers (`--strict-markers`) and coverage enforcement via `pytest-cov`
- Layered test suite: pure unit tests for domain/application, integration tests with SQLAlchemy UoW, E2E CLI smoke checks
- Mandatory tests for new behaviors plus regression coverage when fixing defects
- Static analysis (mypy strict, Ruff) runs alongside pytest in CI

### Git Workflow
- Conventional Commits for all commit messages (`feat:`, `fix:`, `refactor:`, etc.)
- Short-lived feature branches (`feature/<name>` or `chore/<name>`) merged via PR after review
- Keep main branch releasable; rebase or squash merges to maintain a linear history
- OpenSpec proposals must be approved before implementation branches begin

## Domain Context
- Double-entry bookkeeping: every transaction must balance to zero across postings
- Core account types: Assets, Liabilities, Equity, Income, Expenses with hierarchical account codes
- Local-first philosophy: all financial data and logs remain on the user's machine
- Import pipelines (e.g., Nubank CSV) normalize raw statements into domain entities; future roadmap includes rules engine and reporting

## Important Constraints
- Preserve clean architecture boundaries—domain layer stays free of infrastructure concerns
- Maintain local/offline operation; avoid introducing mandatory cloud services
- Enforce domain invariants (balanced transactions, valid account structures) at all entry points
- Preserve structured logging and audit trail expectations when adding new flows
- Favor small, incremental changes (<100 lines) unless justified by spec

## External Dependencies
- SQLite (default persistence) via SQLAlchemy; switchable through repository implementations
- Alembic for schema migrations and DB lifecycle management
- Structured logging and observability via structlog + Rich console output
- Optional Pydantic AI adapters for natural-language CLI experiments (behind feature flags)
