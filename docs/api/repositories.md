# API: Repositories

Repository interfaces abstract persistence details.

Common interfaces:

- `IAccountRepository` — find/save accounts
- `ITransactionRepository` — persist transactions and query by filters
- `IImportBatchRepository` — track import batches and dedupe

Implementations (SQLAlchemy) live in `infrastructure/persistence/` and are tested by integration tests.