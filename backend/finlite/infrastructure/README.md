# Infrastructure Layer

Esta camada contém **adaptadores e implementações** de interfaces definidas no domínio.

## Princípios

- ✅ **Implementa abstrações do domain** (repositories, services)
- ✅ **Esconde detalhes técnicos** (SQL, JSON, HTTP, LLM)
- ✅ **Substituível** (trocar SQLite → Postgres transparente)
- ✅ **Pode ter dependências externas** (SQLAlchemy, requests, pydantic-ai)

## Estrutura

```
infrastructure/
├── persistence/
│   ├── sqlalchemy/
│   │   ├── models.py          # ORM models (SQLAlchemy)
│   │   ├── repositories.py    # Repository implementations
│   │   ├── unit_of_work.py    # UnitOfWork implementation
│   │   └── mappers.py         # Domain ↔ ORM mappers
│   │
│   └── json/
│       └── rules_repository.py  # Rules stored as JSON
│
├── llm/
│   └── pydantic_ai_adapter.py   # LLM intent parser
│
├── events/
│   ├── event_bus.py             # EventBus interface + implementation
│   └── handlers.py              # AuditLogHandler, etc.
│
└── observability/
    ├── logging.py               # Structured logging (structlog)
    └── metrics.py               # Metrics (optional)
```

## Exemplo: SQLAlchemy Repository

```python
# infrastructure/persistence/sqlalchemy/repositories.py
from finlite.domain.entities import Account
from finlite.domain.repositories import AccountRepository
from sqlalchemy.orm import Session

class SqlAlchemyAccountRepository(AccountRepository):
    def __init__(self, session: Session):
        self._session = session
    
    def save(self, account: Account) -> Account:
        """Persist account and return saved entity with id."""
        # Mapper converte domain → ORM
        model = AccountMapper.to_orm(account)
        self._session.add(model)
        self._session.flush()
        # Mapper converte ORM → domain
        return AccountMapper.to_domain(model)
    
    def find_by_id(self, account_id: int) -> Account | None:
        model = self._session.get(AccountModel, account_id)
        return AccountMapper.to_domain(model) if model else None
    
    def find_by_name(self, name: str) -> Account | None:
        model = self._session.execute(
            select(AccountModel).where(AccountModel.name == name)
        ).scalar_one_or_none()
        return AccountMapper.to_domain(model) if model else None
```

## Exemplo: UnitOfWork

```python
# infrastructure/persistence/sqlalchemy/unit_of_work.py
from finlite.domain.repositories import UnitOfWork

class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self._session = None
    
    def __enter__(self):
        self._session = self._session_factory()
        self.accounts = SqlAlchemyAccountRepository(self._session)
        self.transactions = SqlAlchemyTransactionRepository(self._session)
        self.import_batches = SqlAlchemyImportBatchRepository(self._session)
        self.statement_entries = SqlAlchemyStatementRepository(self._session)
        return self
    
    def __exit__(self, *args):
        self._session.close()
    
    def commit(self):
        self._session.commit()
    
    def rollback(self):
        self._session.rollback()
```

## Exemplo: Event Bus

```python
# infrastructure/events/event_bus.py
from finlite.domain.events import DomainEvent

class InMemoryEventBus:
    def __init__(self):
        self._handlers = {}
    
    def subscribe(self, event_type: type, handler):
        self._handlers.setdefault(event_type, []).append(handler)
    
    def publish(self, event: DomainEvent):
        for handler in self._handlers.get(type(event), []):
            handler.handle(event)

# infrastructure/events/handlers.py
class AuditLogHandler:
    def handle(self, event: DomainEvent):
        logger.info("audit_event", **asdict(event))
```

## Mappers (Domain ↔ ORM)

```python
# infrastructure/persistence/sqlalchemy/mappers.py
class AccountMapper:
    @staticmethod
    def to_domain(model: AccountModel) -> Account:
        return Account(
            id=model.id,
            name=AccountName(model.name),
            type=model.type,
            currency=model.currency,
            parent_id=model.parent_id,
            is_archived=model.is_archived,
        )
    
    @staticmethod
    def to_orm(entity: Account) -> AccountModel:
        return AccountModel(
            id=entity.id,
            name=entity.name.value,
            type=entity.type,
            currency=entity.currency,
            parent_id=entity.parent_id,
            is_archived=entity.is_archived,
        )
```

## Structured Logging

```python
# infrastructure/observability/logging.py
import structlog

def setup_logging(debug: bool = False):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )

logger = structlog.get_logger()

# Uso:
logger.info("import_started", file_path=str(path), batch_id=None)
logger.info("import_completed", batch_id=42, entries_count=120)
```

## Testes

Infrastructure é testada com **testes de integração** (banco real, in-memory):

```python
def test_sqlalchemy_account_repository_roundtrip(db_session):
    # Arrange
    repo = SqlAlchemyAccountRepository(db_session)
    account = Account.create(name="Assets:Bank", type=AccountType.ASSET, currency="BRL")
    
    # Act
    saved = repo.save(account)
    found = repo.find_by_id(saved.id)
    
    # Assert
    assert found.name == account.name
    assert found.type == account.type
```

## Regras

1. **Nunca expor ORM models fora desta camada** - sempre retornar domain entities
2. **Repositories não fazem lógica de negócio** - apenas CRUD + queries
3. **UnitOfWork encapsula transação** - application layer controla commit/rollback
4. **Event handlers são assíncronos (idealmente)** - não bloquear use case

---

**Ver também**: `domain/repositories/` (interfaces), `application/` (use cases)
