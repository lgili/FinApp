# Infrastructure Layer

The infrastructure layer implements concrete technologies: database, event bus, logging, external integrations.

## Components

- SQLAlchemy repositories (persistence)
- InMemoryEventBus (development)
- Structlog for structured logging
- LLM adapters (optional)

Implementations must satisfy interfaces defined in domain/application layers to allow testing and swapping.