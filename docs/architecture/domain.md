# Domain Layer

The domain layer contains pure business rules: entities, value objects, domain events, and domain services.

## Key Concepts

- Entities: `Account`, `Transaction`, `Posting`
- Value Objects: `Money`, `AccountType`
- Domain Events: `AccountCreated`, `TransactionRecorded`

## Tests

Domain tests are pure unit tests and do not touch the database.

See `backend/finlite/domain/` for implementation and `tests/unit/domain/` for tests.