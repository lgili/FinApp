# Application Layer

The application layer contains Use Cases which orchestrate operations using repositories and domain objects.

## Examples of Use Cases

- `CreateAccountUseCase`
- `RecordTransactionUseCase`
- `ImportStatementUseCase`

Use Cases should depend only on repository interfaces and domain types. They are the recommended integration points for CLI, API or TUI adapters.