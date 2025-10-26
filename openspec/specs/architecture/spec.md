# Architecture

## Purpose
Define the structural rules that keep Finlite aligned with Clean Architecture, ensuring layers remain isolated, dependencies flow inward, and cross-cutting services (DI, events) operate consistently.

## Requirements
### Requirement: Clean Architecture Layering
The system MUST organize code into four isolated layers (Interfaces, Application, Domain, Infrastructure) that depend inward only.

#### Scenario: Application only depends on domain contracts
- **GIVEN** an application use case (e.g., `RecordTransactionUseCase`)
- **WHEN** reviewing its imports
- **THEN** it references domain entities or repository interfaces only
- **AND** it does not import infrastructure adapters directly

#### Scenario: Interfaces delegate to application services
- **GIVEN** a CLI command such as `fin transactions create`
- **WHEN** the command executes
- **THEN** it calls an application-layer service through the dependency injector
- **AND** the command contains no persistence or domain invariants logic

### Requirement: Dependency Injection Container
The project MUST use a dependency injection container to compose infrastructure adapters and expose them to interfaces at runtime.

#### Scenario: CLI bootstrap uses DI container
- **GIVEN** the CLI entry point
- **WHEN** the application starts
- **THEN** it initializes the shared dependency-injector container
- **AND** resolves repositories and unit-of-work instances through the container

### Requirement: Domain Events and Event Bus
The system MUST publish domain events through an in-memory event bus and attach handlers for audit logging and metrics.

#### Scenario: Transaction emits audit event
- **GIVEN** a transaction is recorded through the application layer
- **WHEN** the transaction is successfully persisted
- **THEN** a domain event (e.g., `TransactionRecordedEvent`) is published on the event bus
- **AND** the registered audit handler logs the event payload using structured logging
