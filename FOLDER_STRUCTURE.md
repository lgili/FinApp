# 📁 Nova Estrutura de Pastas — Finlite v0.2

```
backend/
│
├── finlite/                           # Código principal (nova arquitetura)
│   │
│   ├── domain/                        # 🟦 DOMAIN LAYER (business logic)
│   │   ├── entities/                  # Entidades com identidade
│   │   │   ├── __init__.py
│   │   │   ├── account.py             # Account entity
│   │   │   ├── transaction.py         # Transaction + validação soma zero
│   │   │   ├── statement.py           # ImportBatch, StatementEntry
│   │   │   └── rule.py                # MapRule entity
│   │   │
│   │   ├── value_objects/             # Objetos sem identidade
│   │   │   ├── __init__.py
│   │   │   ├── money.py               # Money(amount, currency)
│   │   │   ├── account_name.py        # AccountName(hierarchical)
│   │   │   └── posting.py             # Posting value object
│   │   │
│   │   ├── exceptions/                # Domain errors
│   │   │   ├── __init__.py
│   │   │   └── accounting.py          # UnbalancedError, InsufficientPostingsError
│   │   │
│   │   ├── repositories/              # Repository interfaces (ABC)
│   │   │   ├── __init__.py
│   │   │   ├── account.py             # AccountRepository (ABC)
│   │   │   ├── transaction.py         # TransactionRepository (ABC)
│   │   │   ├── statement.py           # StatementRepository (ABC)
│   │   │   └── unit_of_work.py        # UnitOfWork (ABC)
│   │   │
│   │   ├── __init__.py
│   │   └── README.md                  # ✅ Documentação da camada
│   │
│   ├── application/                   # 🟩 APPLICATION LAYER (use cases)
│   │   ├── accounts/
│   │   │   ├── __init__.py
│   │   │   ├── create_account.py      # Use case: criar conta
│   │   │   ├── list_accounts.py       # Use case: listar contas
│   │   │   └── seed_default_chart.py  # Use case: seed plano de contas
│   │   │
│   │   ├── transactions/
│   │   │   ├── __init__.py
│   │   │   ├── create_transaction.py  # Use case: criar transação
│   │   │   └── list_transactions.py   # Use case: listar transações
│   │   │
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── import_nubank.py       # Use case: importar Nubank CSV
│   │   │   ├── import_ofx.py          # Use case: importar OFX
│   │   │   ├── apply_rules.py         # Use case: aplicar regras
│   │   │   └── post_pending.py        # Use case: postar entries
│   │   │
│   │   ├── reports/
│   │   │   ├── __init__.py
│   │   │   ├── generate_cashflow.py   # Use case: relatório cashflow
│   │   │   └── generate_category_report.py
│   │   │
│   │   ├── export/
│   │   │   ├── __init__.py
│   │   │   └── export_beancount.py    # Use case: export Beancount
│   │   │
│   │   ├── nlp/
│   │   │   ├── __init__.py
│   │   │   ├── parse_intent.py        # Use case: NL → intent
│   │   │   └── execute_intent.py      # Use case: executar intent
│   │   │
│   │   ├── __init__.py
│   │   └── README.md                  # ✅ Documentação da camada
│   │
│   ├── infrastructure/                # 🟨 INFRASTRUCTURE LAYER (adapters)
│   │   ├── persistence/
│   │   │   ├── sqlalchemy/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py          # ORM models (migrar de legacy)
│   │   │   │   ├── repositories.py    # Repository implementations
│   │   │   │   ├── unit_of_work.py    # UnitOfWork SQLAlchemy
│   │   │   │   ├── mappers.py         # Domain ↔ ORM mappers
│   │   │   │   └── session.py         # Session factory
│   │   │   │
│   │   │   └── json/
│   │   │       ├── __init__.py
│   │   │       └── rules_repository.py # Rules em JSON
│   │   │
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   └── pydantic_ai_adapter.py # LLM intent parser
│   │   │
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── event_bus.py           # EventBus interface + impl
│   │   │   └── handlers.py            # AuditLogHandler, etc.
│   │   │
│   │   ├── observability/
│   │   │   ├── __init__.py
│   │   │   ├── logging.py             # Structured logging (structlog)
│   │   │   └── metrics.py             # Métricas (opcional)
│   │   │
│   │   ├── __init__.py
│   │   └── README.md                  # ✅ Documentação da camada
│   │
│   ├── interfaces/                    # 🟧 INTERFACES LAYER (entrypoints)
│   │   ├── cli/
│   │   │   ├── commands/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── accounts.py        # Comandos de contas
│   │   │   │   ├── transactions.py    # Comandos de transações
│   │   │   │   ├── import.py          # Comandos de import
│   │   │   │   ├── post.py            # Comandos de post
│   │   │   │   ├── rules.py           # Comandos de regras
│   │   │   │   ├── reports.py         # Comandos de relatórios
│   │   │   │   ├── export.py          # Comandos de export
│   │   │   │   └── ask.py             # Comando NL (fin ask)
│   │   │   │
│   │   │   ├── presenters/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── account_presenter.py
│   │   │   │   ├── transaction_presenter.py
│   │   │   │   ├── import_presenter.py
│   │   │   │   └── report_presenter.py
│   │   │   │
│   │   │   ├── __init__.py
│   │   │   └── app.py                 # Entrypoint Typer principal
│   │   │
│   │   ├── api/                       # (Fase 11) FastAPI
│   │   │   └── __init__.py
│   │   │
│   │   ├── tui/                       # (Fase 2B) Textual
│   │   │   └── __init__.py
│   │   │
│   │   ├── __init__.py
│   │   └── README.md                  # ✅ Documentação da camada
│   │
│   ├── shared/                        # 🟪 SHARED (cross-cutting)
│   │   ├── __init__.py
│   │   ├── config.py                  # Settings (migrar de legacy)
│   │   ├── di.py                      # Dependency Injection container
│   │   └── types.py                   # Type aliases comuns
│   │
│   └── __init__.py
│
├── tests/                             # Testes (nova estrutura em pirâmide)
│   ├── unit/
│   │   ├── domain/                    # Testes puros (sem DB)
│   │   │   ├── __init__.py
│   │   │   ├── test_account.py
│   │   │   ├── test_transaction.py
│   │   │   └── test_money.py
│   │   │
│   │   ├── application/               # Mock repositories
│   │   │   ├── __init__.py
│   │   │   ├── test_import_nubank.py
│   │   │   └── test_create_transaction.py
│   │   │
│   │   └── __init__.py
│   │
│   ├── integration/                   # Com banco (in-memory SQLite)
│   │   ├── __init__.py
│   │   ├── test_repositories.py
│   │   ├── test_unit_of_work.py
│   │   └── test_import_workflow.py
│   │
│   ├── e2e/                           # CLI completo (subprocess)
│   │   ├── __init__.py
│   │   └── test_full_workflow.py
│   │
│   ├── conftest.py                    # Fixtures compartilhadas
│   └── __init__.py
│
├── finlite_legacy/                    # 🗂️ BACKUP (código antigo)
│   └── ...                            # (todo código original preservado)
│
├── tests_legacy/                      # 🗂️ BACKUP (testes antigos)
│   └── ...                            # (todos testes originais preservados)
│
├── alembic/                           # Migrations (mantém intacto)
│   ├── env.py
│   ├── versions/
│   │   └── 0001_initial.py
│   └── ...
│
├── scripts/                           # Scripts auxiliares
│   └── ...
│
├── var/                               # Data dir (runtime)
│   └── data/
│       └── finlite.db
│
├── pyproject.toml                     # ✅ Atualizado (v0.2.0, novas deps)
├── alembic.ini
├── Makefile
├── README.md
└── QUICKSTART_NEW_ARCH.md             # ✅ Guia de início rápido

```

---

## 📊 Estatísticas

**Pastas criadas:** 24  
**Documentação:** 6 arquivos README  
**Código legado preservado:** 100%  
**Compatibilidade migrations:** ✅ Alembic mantido  

---

## 🎨 Legenda de Cores (Camadas)

- 🟦 **Domain** - Lógica de negócio pura (sem dependências)
- 🟩 **Application** - Use cases (orquestra domain + repos)
- 🟨 **Infrastructure** - Adapters (DB, LLM, eventos)
- 🟧 **Interfaces** - Entrypoints (CLI, API, TUI)
- 🟪 **Shared** - Cross-cutting (config, DI, types)

---

## 🔄 Fluxo de Dependências

```
Interfaces  →  Application  →  Domain
    ↓              ↓             ↑
Infrastructure  ←──────────────┘
```

**Regra de ouro:** 
- Domain não depende de ninguém
- Infrastructure implementa abstrações do Domain
- Application orquestra Domain + Infrastructure
- Interfaces chamam Application

---

## ✅ Próximos Arquivos a Criar

### Prioridade 1 (Domain)
- `domain/entities/account.py`
- `domain/entities/transaction.py`
- `domain/value_objects/money.py`
- `domain/exceptions/accounting.py`

### Prioridade 2 (Infrastructure)
- `infrastructure/persistence/sqlalchemy/models.py` (copiar de legacy)
- `infrastructure/persistence/sqlalchemy/repositories.py`
- `infrastructure/persistence/sqlalchemy/unit_of_work.py`

### Prioridade 3 (Application)
- `application/ingestion/import_nubank.py`
- `application/accounts/create_account.py`

### Prioridade 4 (Interfaces)
- `interfaces/cli/commands/import.py`
- `shared/di.py`

---

**Ver:** `MIGRATION_ROADMAP.md` para checklist completo por fase! 🚀
