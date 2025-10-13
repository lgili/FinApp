# Event Bus

Finlite uses a publish/subscribe event bus to decouple side effects from core business logic.

## Domain Events

Examples:

- `AccountCreated`
- `TransactionRecorded`

## Handlers

- `AuditLogHandler`: writes audit entries
- `ConsoleEventHandler`: development output
- `MetricsEventHandler`: increments monitoring counters

Event handlers should be idempotent and resilient to errors.