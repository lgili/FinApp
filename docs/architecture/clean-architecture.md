# Clean Architecture

Finlite follows Clean Architecture to keep business logic independent from frameworks and infrastructure.

## Principles

- Dependency rule: inner layers do not depend on outer layers
- Use Cases orchestrate domain logic
- Infrastructure implements interfaces defined by the domain/application

Read the overview for diagrams: [Architecture Overview](overview.md).

## How we apply it

- Domain layer: entities, value objects, domain events
- Application layer: use cases and DTOs
- Infrastructure layer: repositories, event bus, logging
- Interface layer: CLI adapters and presenters

See detailed pages for each layer: `domain.md`, `application.md`, `infrastructure.md`.