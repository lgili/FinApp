# 🏛️ Arquitetura Finlite v0.2 — Clean Architecture

Este documento descreve a nova arquitetura do Finlite, baseada em **Clean/Hexagonal Architecture**.

---

## 📐 Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                        Interfaces                            │
│  (CLI, API, TUI — thin adapters, presentation logic)         │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │    CLI     │  │    API     │  │    TUI     │            │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘            │
└────────┼────────────────┼────────────────┼──────────────────┘
         │                │                │
         └────────────────┴────────────────┘
                          │
         ┌────────────────▼────────────────┐
         │        Application Layer         │
         │  (Use Cases, orchestration)      │
         │                                  │
         │  • import_nubank()               │
         │  • create_transaction()          │
         │  • generate_cashflow()           │
         │  • apply_rules()                 │
         └────────────┬─────────────────────┘
                      │
         ┌────────────▼─────────────────────┐
         │         Domain Layer              │
         │  (Entities, Value Objects, Rules) │
         │                                   │
         │  • Account                        │
         │  • Transaction + Posting          │
         │  • ImportBatch, StatementEntry    │
         │  • MapRule                        │
         └────────────┬──────────────────────┘
                      │
         ┌────────────▼──────────────────────┐
         │      Infrastructure Layer          │
         │  (DB, Files, LLM, Events)          │
         │                                    │
         │  • SqlAlchemyUnitOfWork            │
         │  • AccountRepository               │
         │  • JsonRulesRepository             │
         │  • PydanticAIAdapter               │
         │  • EventBus + Handlers             │
         └────────────────────────────────────┘
```

---

## 📦 Estrutura de Pastas

```
backend/
├── finlite/
│   ├── domain/                    # Camada de Domínio (business logic)
│   │   ├── entities/              # Account, Transaction, etc.
│   │   ├── value_objects/         # Money, AccountName, Posting
│   │   ├── exceptions/            # UnbalancedError, etc.
│   │   └── repositories/          # Interfaces (ABC)
│   │
│   ├── application/               # Camada de Aplicação (use cases)
│   │   ├── accounts/              # create_account, list_accounts
│   │   ├── transactions/          # create_transaction
│   │   ├── ingestion/             # import_nubank, apply_rules
│   │   ├── reports/               # generate_cashflow
│   │   ├── export/                # export_beancount
│   │   └── nlp/                   # parse_intent, execute_intent
│   │
│   ├── infrastructure/            # Camada de Infraestrutura (adapters)
│   │   ├── persistence/
│   │   │   ├── sqlalchemy/        # Models, Repositories, UoW
│   │   │   └── json/              # JsonRulesRepository
│   │   ├── llm/                   # PydanticAIAdapter
│   │   ├── events/                # EventBus, AuditLogHandler
│   │   └── observability/         # Structured logging, metrics
│   │
│   ├── interfaces/                # Camada de Interface (entrypoints)
│   │   ├── cli/
│   │   │   ├── commands/          # Typer commands (thin)
│   │   │   └── presenters/        # Rich output formatting
│   │   ├── api/                   # FastAPI (Fase 11)
│   │   └── tui/                   # Textual (Fase 2B)
│   │
│   └── shared/                    # Cross-cutting concerns
│       ├── config.py              # Settings (Pydantic)
│       ├── di.py                  # Dependency Injection
│       └── types.py               # Common type aliases
│
├── tests/
│   ├── unit/
│   │   ├── domain/                # Testes puros (sem DB)
│   │   └── application/           # Mock repositories
│   ├── integration/               # Com banco (in-memory)
│   └── e2e/                       # CLI completo (subprocess)
│
├── finlite_legacy/                # Backup do código antigo
├── tests_legacy/                  # Backup dos testes antigos
├── alembic/                       # Migrations (mantém)
├── pyproject.toml
└── README.md
```

---

## 🎯 Responsabilidades por Camada

### 1️⃣ Domain Layer

**O QUE FAZ:**
- Define **entidades** (Account, Transaction) com **lógica de negócio**
- Valida **regras invariantes** (ex: soma zero, mínimo 2 postings)
- Define **interfaces de repositories** (ABC)
- **Sem dependências externas** (apenas stdlib)

**O QUE NÃO FAZ:**
- ❌ Não acessa banco de dados
- ❌ Não faz parsing de CSV/JSON
- ❌ Não conhece HTTP, CLI, ou LLM

**EXEMPLO:**
```python
# domain/entities/transaction.py
@dataclass(frozen=True)
class Transaction:
    @classmethod
    def create(cls, description, postings, ...) -> "Transaction":
        # Valida soma zero
        if sum(p.amount for p in postings) != 0:
            raise UnbalancedTransactionError()
        return cls(...)
```

---

### 2️⃣ Application Layer

**O QUE FAZ:**
- **Orquestra** use cases (import → rules → post)
- **Coordena** domain entities + repositories
- **Emite eventos** para auditoria
- **Controla transações** via UnitOfWork

**O QUE NÃO FAZ:**
- ❌ Não contém lógica de negócio (delega para domain)
- ❌ Não conhece detalhes de DB (usa repositories)
- ❌ Não formata output (retorna DTOs)

**EXEMPLO:**
```python
# application/ingestion/import_nubank.py
def import_nubank(cmd: ImportNubankCommand, uow: UnitOfWork, event_bus: EventBus):
    with uow:
        # 1. Validar
        # 2. Parse CSV
        # 3. Criar domain entities
        batch = ImportBatch.create(...)
        # 4. Persistir via repository
        uow.import_batches.save(batch)
        # 5. Commit
        uow.commit()
        # 6. Emitir evento
        event_bus.publish(ImportCompletedEvent(...))
```

---

### 3️⃣ Infrastructure Layer

**O QUE FAZ:**
- **Implementa** repositories (SQLAlchemy, JSON)
- **Esconde** detalhes técnicos (SQL, HTTP)
- **Mappers** (Domain ↔ ORM)
- **Event handlers** (logging, hooks)

**O QUE NÃO FAZ:**
- ❌ Não contém lógica de negócio
- ❌ Não expõe ORM models fora da camada

**EXEMPLO:**
```python
# infrastructure/persistence/sqlalchemy/repositories.py
class SqlAlchemyAccountRepository(AccountRepository):
    def save(self, account: Account) -> Account:
        model = AccountMapper.to_orm(account)
        self._session.add(model)
        self._session.flush()
        return AccountMapper.to_domain(model)
```

---

### 4️⃣ Interfaces Layer

**O QUE FAZ:**
- **Adapta** entrada/saída (CLI, API, TUI)
- **Parse** argumentos (Typer, FastAPI)
- **Apresenta** resultados (Rich, JSON)
- **Injeta** dependências via DI

**O QUE NÃO FAZ:**
- ❌ Não contém lógica de negócio (chama use cases)
- ❌ Não acessa banco direto

**EXEMPLO:**
```python
# interfaces/cli/commands/import.py
@import_app.command("nubank")
def import_nubank_cmd(file_path: Path):
    container = get_container()
    result = container.import_nubank_use_case()(
        ImportNubankCommand(file_path=file_path, ...)
    )
    ImportPresenter.show_success(result)  # Rich table
```

---

## 🔄 Fluxo de Execução (Exemplo)

**Comando:** `fin import nubank extrato.csv`

```
1. CLI (interfaces/cli/commands/import.py)
   ↓ parse args → ImportNubankCommand
   
2. DI Container (shared/di.py)
   ↓ resolve → import_nubank use case + UoW + EventBus
   
3. Application (application/ingestion/import_nubank.py)
   ↓ orquestra → valida, parse, cria entities
   
4. Domain (domain/entities/import_batch.py)
   ↓ valida → ImportBatch.create(...)
   
5. Infrastructure (infrastructure/persistence/sqlalchemy/)
   ↓ persiste → uow.import_batches.save(batch)
   
6. Infrastructure (infrastructure/events/)
   ↓ audit → event_bus.publish(ImportCompletedEvent)
   
7. CLI Presenter (interfaces/cli/presenters/)
   ↓ formata → Rich table com resultado
```

---

## 🧪 Estratégia de Testes

### Pirâmide de Testes

```
      /\
     /E2E\      ← Poucos (CLI completo, workflows)
    /──────\
   /Integr.\   ← Médio (repositories, UoW, com DB)
  /──────────\
 /   Unit     \ ← Muitos (domain, mocked repos)
/──────────────\
```

### Tipos de Teste

1. **Unit (domain)** - Sem I/O, rápidos
   ```python
   def test_transaction_rejects_unbalanced():
       with pytest.raises(UnbalancedTransactionError):
           Transaction.create(...)
   ```

2. **Unit (application)** - Mock repositories
   ```python
   def test_import_nubank_detects_duplicate():
       mock_uow = MockUnitOfWork()
       mock_uow.import_batches.add(existing)
       with pytest.raises(DuplicateImportError):
           import_nubank(..., uow=mock_uow)
   ```

3. **Integration** - DB real (in-memory SQLite)
   ```python
   def test_repository_roundtrip(db_session):
       repo = SqlAlchemyAccountRepository(db_session)
       account = Account.create(...)
       saved = repo.save(account)
       assert repo.find_by_id(saved.id) == account
   ```

4. **E2E** - CLI completo
   ```python
   def test_full_workflow():
       runner.invoke(app, ["import", "nubank", "file.csv"])
       runner.invoke(app, ["rules", "apply"])
       result = runner.invoke(app, ["report", "cashflow"])
       assert "Total" in result.stdout
   ```

---

## 🔧 Dependency Injection

**Container centralizado** (`shared/di.py`):

```python
class Container(containers.DeclarativeContainer):
    config = providers.Singleton(get_settings)
    session_factory = providers.Singleton(create_session_factory, ...)
    uow = providers.Factory(SqlAlchemyUnitOfWork, ...)
    event_bus = providers.Singleton(InMemoryEventBus)
    
    # Use cases
    import_nubank_use_case = providers.Factory(
        import_nubank,
        uow=uow,
        event_bus=event_bus,
    )
```

**Uso no CLI:**
```python
container = get_container()
result = container.import_nubank_use_case()(command)
```

---

## 📊 Benefícios da Nova Arquitetura

| Benefício | Antes (Legacy) | Depois (Clean) |
|-----------|----------------|----------------|
| **Testabilidade** | Testes acoplados ao DB | Unit tests puros (domain) |
| **Manutenibilidade** | Lógica espalhada no CLI | Separação clara de responsabilidades |
| **Reuso** | Código duplicado CLI/API | Use cases compartilhados |
| **Substituibilidade** | SQLite hardcoded | Trocar DB via repositories |
| **Extensibilidade** | Difícil adicionar hooks | Event Bus + handlers |
| **Observabilidade** | Logs básicos | Structured logging + traces |

---

## 🚀 Próximos Passos

Ver [`MIGRATION_ROADMAP.md`](../../MIGRATION_ROADMAP.md) para checklist detalhado.

**Ordem de migração recomendada:**
1. ✅ Estrutura de pastas (FEITO)
2. → Domain entities (Transaction, Account)
3. → Repositories + UnitOfWork
4. → Application use cases (import_nubank)
5. → CLI refatorado (thin adapters)
6. → Event Bus + structured logging
7. → Testes migrados

---

## 📚 Referências

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture (Alistair Cockburn)](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design (Eric Evans)](https://www.domainlanguage.com/ddd/)
- [Repository Pattern (Martin Fowler)](https://martinfowler.com/eaaCatalog/repository.html)
- [Unit of Work Pattern](https://martinfowler.com/eaaCatalog/unitOfWork.html)

---

**Última atualização:** 2025-10-11  
**Versão:** 0.2.0
