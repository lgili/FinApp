# 🗺️ Roadmap de Migração — Arquitetura Clean/Hexagonal

**Data início**: 2025-10-11  
**Objetivo**: Refatorar Finlite para arquitetura em camadas (Domain → Application → Infrastructure → Interfaces)

---

## 📋 Checklist Geral

### Fase 0: Estrutura e Fundação (2-3 dias)
- [ ] ✅ Backup código legado (`finlite_legacy/`, `tests_legacy/`)
- [ ] ✅ Criar nova estrutura de pastas
- [ ] ✅ Configurar nova estrutura no `pyproject.toml`
- [ ] Migrar `config.py` para `shared/`
- [ ] Migrar `logging.py` para `shared/observability/`
- [ ] Setup Dependency Injection container
- [ ] Configurar structured logging (structlog)

### Fase 1: Domain Layer - Entidades Puras (2-3 dias) ✅ **COMPLETA**
- [x] Criar entidades de domínio puras
  - [x] `Account` entity (22 testes ✅)
  - [x] `Transaction` entity (22 testes ✅)
  - [x] `Posting` value object
  - [x] `ImportBatch` entity
- [x] Criar value objects
  - [x] `Money` (amount + currency) (38 testes ✅)
  - [x] `AccountType` enum
- [x] Criar domain exceptions
  - [x] `UnbalancedTransactionError`
  - [x] `InvalidAccountTypeError`
  - [x] `DuplicateAccountError`
  - [x] `AccountNotFoundError`
  - [x] `TransactionNotFoundError`
- [x] Criar repository interfaces (ABC)
  - [x] `IAccountRepository`
  - [x] `ITransactionRepository`
  - [x] `IImportBatchRepository`
- [x] Testes unitários de domínio (82 testes passando ✅)

**Status:** ✅ 100% Completo (2025-10-12)

### Fase 2: Infrastructure Layer - Persistence (4-5 dias)
- [ ] Migrar modelos SQLAlchemy para `infrastructure/persistence/sqlalchemy/models.py`
- [ ] Criar Repository abstratos
  - [ ] `AccountRepository` (ABC)
  - [ ] `TransactionRepository` (ABC)
  - [ ] `StatementRepository` (ABC)
  - [ ] `RulesRepository` (ABC)
- [ ] Implementar Repositories SQLAlchemy
  - [ ] `SqlAlchemyAccountRepository`
  - [ ] `SqlAlchemyTransactionRepository`
  - [ ] `SqlAlchemyStatementRepository`
- [ ] Implementar `UnitOfWork` pattern
  - [ ] `UnitOfWork` (ABC)
  - [ ] `SqlAlchemyUnitOfWork`
- [ ] Criar mappers (Domain ↔ ORM)
  - [ ] `AccountMapper`
  - [ ] `TransactionMapper`
- [ ] Testes de integração (repositories)

### Fase 3: Infrastructure Layer - Outros Adapters (2-3 dias)
- [ ] Migrar rules para `infrastructure/persistence/json/`
  - [ ] `JsonRulesRepository`
- [ ] Migrar LLM agent para `infrastructure/llm/`
  - [ ] `PydanticAIAdapter`
- [ ] Criar Event Bus
  - [ ] `EventBus` (ABC)
  - [ ] `InMemoryEventBus`
  - [ ] `AuditLogHandler`
- [ ] Setup observability
  - [ ] Structured logging (structlog)
  - [ ] Métricas básicas (opcional)

### Fase 4: Application Layer - Use Cases (5-7 dias)
- [ ] **Accounts Use Cases**
  - [ ] `create_account.py`
  - [ ] `list_accounts.py`
  - [ ] `seed_default_chart.py`
- [ ] **Transactions Use Cases**
  - [ ] `create_transaction.py`
  - [ ] `list_transactions.py`
- [ ] **Ingestion Use Cases**
  - [ ] `import_nubank.py`
  - [ ] `import_ofx.py`
  - [ ] `apply_rules.py`
  - [ ] `post_pending.py`
- [ ] **Reports Use Cases**
  - [ ] `generate_cashflow.py`
  - [ ] `generate_category_report.py`
- [ ] **Export Use Cases**
  - [ ] `export_beancount.py`
- [ ] **NLP Use Cases**
  - [ ] `parse_intent.py`
  - [ ] `execute_intent.py`
- [ ] Testes de use cases (mocking repositories)

### Fase 5: Interfaces Layer - CLI (3-4 dias)
- [ ] Refatorar CLI para thin adapters
  - [ ] `commands/accounts.py`
  - [ ] `commands/transactions.py`
  - [ ] `commands/import.py`
  - [ ] `commands/post.py`
  - [ ] `commands/rules.py`
  - [ ] `commands/reports.py`
  - [ ] `commands/export.py`
  - [ ] `commands/ask.py`
- [ ] Criar presenters (Rich output)
  - [ ] `AccountPresenter`
  - [ ] `TransactionPresenter`
  - [ ] `ReportPresenter`
- [ ] Integrar Dependency Injection no CLI
- [ ] Testes end-to-end (CLI runner)

### Fase 6: Testes e Qualidade (2-3 dias)
- [ ] Migrar testes relevantes de `tests_legacy/`
- [ ] Adicionar testes de integração workflows
  - [ ] Import → Rules → Post → Report
  - [ ] Create accounts → Add transactions → Generate report
- [ ] Garantir coverage ≥ 80%
- [ ] Performance benchmarks
  - [ ] 50k postings < 2s (relatório)
- [ ] Golden tests para relatórios

### Fase 7: Documentação e Finalização (1-2 dias)
- [ ] Atualizar README.md
- [ ] Criar ADR-0002 (Clean Architecture)
- [ ] Documentar estrutura de pastas
- [ ] Guia de contribuição
- [ ] Exemplos de uso
- [ ] Remover código legado (ou mover para branch)

---

## 📊 Status Atual

**Progresso Geral**: 2/7 fases (28%)

```
Fase 0: ██████░░░░ 60%
Fase 1: ░░░░░░░░░░  0%
Fase 2: ░░░░░░░░░░  0%
Fase 3: ░░░░░░░░░░  0%
Fase 4: ░░░░░░░░░░  0%
Fase 5: ░░░░░░░░░░  0%
Fase 6: ░░░░░░░░░░  0%
Fase 7: ░░░░░░░░░░  0%
```

---

## 🎯 Prioridades de Migração

### P0 (Crítico - não quebra funcionalidade existente)
1. Domain entities + repositories
2. UnitOfWork
3. Application services principais (import, post, report)
4. CLI adapters

### P1 (Importante - melhora qualidade)
1. Event Bus + auditoria
2. Structured logging
3. Dependency Injection
4. Testes de integração

### P2 (Nice to have - pode ser depois)
1. Performance benchmarks
2. Golden tests
3. Documentação extensa
4. Métricas/observabilidade avançada

---

## 🚀 Como Usar Este Roadmap

1. **Marcar progresso**: Trocar `[ ]` por `[x]` conforme completar tarefas
2. **Branches**: Criar branch por fase (`feat/phase-1-domain`, etc.)
3. **Commits atômicos**: 1 commit = 1 checkbox
4. **PR Reviews**: Revisar cada fase antes de mergear
5. **Testes sempre**: Não mergear sem testes passando

---

## 📝 Notas de Migração

### Mantido da Versão Legado
- ✅ Modelos SQLAlchemy (migrando para infrastructure)
- ✅ Migrações Alembic (compatíveis)
- ✅ Configuração Pydantic Settings
- ✅ Testes de aceitação Phase 2
- ✅ Dataset de exemplo

### Novo na Arquitetura Clean
- 🆕 Domain entities separadas de ORM
- 🆕 Repository pattern explícito
- 🆕 UnitOfWork para transações
- 🆕 Application services (use cases)
- 🆕 Event Bus para auditoria
- 🆕 Dependency Injection
- 🆕 Structured logging

### Melhorias de Qualidade
- 📈 Testes unitários puros (sem DB)
- 📈 Separação clara de responsabilidades
- 📈 Facilita testar (mock repositories)
- 📈 Preparado para API/TUI sem duplicar código
- 📈 Observabilidade estruturada

---

## 🔗 Links Úteis

- [Plan.md original](./plan.md)
- [ADR-0001: Arquitetura fundacional](./docs/ADRs/ADR-0001.md)
- [Código legado](./backend/finlite_legacy/)
- [Testes legado](./backend/tests_legacy/)

---

**Última atualização**: 2025-10-11  
**Responsável**: @lgili
