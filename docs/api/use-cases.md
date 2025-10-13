# API: Use Cases

This page documents the public Use Cases exposed by the application layer. Use Cases are callable from CLI, API or TUI adapters.

## Notable Use Cases

- `CreateAccountUseCase` — create a new account
- `RecordTransactionUseCase` — record a balanced transaction
- `ImportStatementUseCase` — import bank statements

Use Cases accept domain DTOs and return domain entities or results. They should be covered by unit tests.