# API: Domain Events

Domain events are immutable facts emitted by use cases.

Common events:

- `AccountCreated` — when an account is created
- `TransactionRecorded` — when a transaction is successfully saved

Events are published to the Event Bus and handled asynchronously (or synchronously in memory). Handlers implement auditing, metrics, and side effects.