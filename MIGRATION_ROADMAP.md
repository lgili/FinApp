# 🗺️ Roadmap de Migração — Arquitetura Clean/Hexagonal

**Data início**: 2025-10-11
**Última atualização**: 2025-10-15
**Objetivo**: Refatorar Finlite para arquitetura em camadas (Domain → Application → Infrastructure → Interfaces)

---

## 📊 Status Atual Geral

**Progresso**: 5/7 fases completas (70%)

```
Fase 0: ████████████ 100% ✅
Fase 1: ████████████ 100% ✅
Fase 2: ████████████ 100% ✅
Fase 3: ████████████ 100% ✅
Fase 4: ██████████░░  85% ⚠️
Fase 5: ████████░░░░  70% ⚠️
Fase 6: ██░░░░░░░░░░  15% 🔜
Fase 7: ░░░░░░░░░░░░   0% 📋
```

---

## 📋 Checklist Detalhado por Fase

### Fase 0: Estrutura e Fundação ✅ **COMPLETA** (100%)

- [x] ✅ Backup código legado (`finlite_legacy/`, `tests_legacy/`)
- [x] ✅ Criar nova estrutura de pastas
- [x] ✅ Configurar nova estrutura no `pyproject.toml`
- [x] ✅ Migrar `config.py` para `shared/`
- [x] ✅ Migrar `logging.py` para `shared/observability/`
- [x] ✅ Setup Dependency Injection container
- [x] ✅ Configurar structured logging (structlog)

**Status**: ✅ 100% Completo (2025-10-11)

---

### Fase 1: Domain Layer - Entidades Puras ✅ **COMPLETA** (100%)

- [x] Criar entidades de domínio puras
  - [x] `Account` entity (22 testes ✅)
  - [x] `Transaction` entity (22 testes ✅)
  - [x] `Posting` value object (17 testes ✅)
  - [x] `ImportBatch` entity (8 testes ✅)
  - [x] `StatementEntry` entity (13 testes ✅)
- [x] Criar value objects
  - [x] `Money` (amount + currency) (38 testes ✅)
  - [x] `AccountType` enum (48 testes ✅)
- [x] Criar domain exceptions
  - [x] `UnbalancedTransactionError`
  - [x] `InvalidAccountTypeError`
  - [x] `DuplicateAccountError`
  - [x] `AccountNotFoundError`
  - [x] `TransactionNotFoundError`
  - [x] `DuplicateImportError`
- [x] Criar repository interfaces (ABC)
  - [x] `IAccountRepository`
  - [x] `ITransactionRepository`
  - [x] `IImportBatchRepository`
  - [x] `IStatementEntryRepository`
- [x] Testes unitários de domínio (82 testes passando ✅)

**Status**: ✅ 100% Completo (2025-10-12)

---

### Fase 2: Infrastructure Layer - Persistence ✅ **COMPLETA** (100%)

- [x] Migrar modelos SQLAlchemy para `infrastructure/persistence/sqlalchemy/models.py`
- [x] Criar Repository abstratos
  - [x] `IAccountRepository` (ABC)
  - [x] `ITransactionRepository` (ABC)
  - [x] `IStatementEntryRepository` (ABC)
  - [x] `IImportBatchRepository` (ABC)
- [x] Implementar Repositories SQLAlchemy
  - [x] `SqlAlchemyAccountRepository` (13 testes ✅)
  - [x] `SqlAlchemyTransactionRepository` (11 testes ✅)
  - [x] `SqlAlchemyStatementEntryRepository` (8 testes ✅)
  - [x] `SqlAlchemyImportBatchRepository` (6 testes ✅)
- [x] Implementar `UnitOfWork` pattern
  - [x] `IUnitOfWork` (ABC)
  - [x] `SqlAlchemyUnitOfWork` (8 testes ✅)
- [x] Criar mappers (Domain ↔ ORM)
  - [x] `AccountMapper` (com UUID-Integer conversion)
  - [x] `TransactionMapper`
  - [x] `StatementEntryMapper`
  - [x] `ImportBatchMapper`
- [x] Testes de integração (repositories) (46 testes ✅)

**Status**: ✅ 100% Completo (2025-10-13)

---

### Fase 3: Infrastructure Layer - Event Bus & Observability ✅ **COMPLETA** (100%)

- [x] Criar Event Bus
  - [x] `IEventBus` (ABC)
  - [x] `InMemoryEventBus` (4 testes ✅)
  - [x] `AuditLogHandler`
  - [x] `MetricsEventHandler`
- [x] Domain Events
  - [x] `AccountCreated`
  - [x] `TransactionRecorded`
  - [x] `StatementImported`
  - [x] `StatementMatched`
  - [x] `StatementPosted`
  - [x] `StatementImportFailed`
- [x] Setup observability
  - [x] Structured logging (structlog)
  - [x] JSON output para produção
  - [x] Debug mode com cores
  - [x] ISO timestamps
  - [x] Exception tracebacks com contexto

**Status**: ✅ 100% Completo (2025-10-14)

---

### Fase 4: Application Layer - Use Cases ⚠️ **EM PROGRESSO** (85%)

#### ✅ Contas (100%)
- [x] `CreateAccountUseCase` (3 testes ✅)
- [x] `ListAccountsUseCase` (7 testes ✅)
- [x] `GetAccountBalanceUseCase` (5 testes ✅)

#### ✅ Transações (100%)
- [x] `RecordTransactionUseCase` (4 testes ✅)
- [x] `ListTransactionsUseCase` (7 testes ✅)

#### ✅ Ingestão (100%)
- [x] `ImportNubankStatementUseCase` (8 testes ✅)
- [x] `ApplyRulesUseCase` (6 testes ✅)
- [x] `PostPendingEntriesUseCase` (9 testes ✅)

#### ✅ Relatórios (100%)
- [x] `GenerateCashflowReportUseCase` (8 testes ✅)

#### ✅ Exportação (100%)
- [x] `ExportBeancountUseCase` (10 testes ✅)

#### 🔜 Pendentes (0%)
- [ ] `ImportOFXUseCase`
- [ ] `BalanceSheetUseCase`
- [ ] `IncomeStatementUseCase`
- [ ] `BuildCardStatementUseCase`
- [ ] `PayCardUseCase`
- [ ] `SetBudgetUseCase`
- [ ] `BudgetReportUseCase`

**Status**: ⚠️ 85% Completo (72 testes passando ✅)

---

### Fase 5: Interfaces Layer - CLI ⚠️ **EM PROGRESSO** (70%)

#### ✅ CLI Core (100%)
- [x] Refatorar CLI para thin adapters
  - [x] `commands/accounts.py` (create, list, balance)
  - [x] `commands/transactions.py` (create, list)
  - [x] `commands/imports.py` (nubank, list, entries)
  - [x] `commands/rules.py` (apply) ✨ NOVO
  - [x] `commands/post.py` (pending) ✨ NOVO
  - [x] `commands/reports.py` (cashflow) ✨ NOVO
  - [x] `commands/export.py` (beancount) ✨ NOVO
- [x] Integrar Dependency Injection no CLI
- [x] Global options (`--debug`, `--json-logs`)
- [x] Error handling com mensagens claras

#### 🔜 Pendentes (0%)
- [ ] `commands/card.py` (build-statement, pay, list)
- [ ] `commands/budget.py` (set, list, report)
- [ ] `commands/ask.py` (NL → Intent)
- [ ] Presenters (Rich output)
  - [ ] `AccountPresenter`
  - [ ] `TransactionPresenter`
  - [ ] `ReportPresenter`
- [ ] Testes end-to-end (CLI runner)

**Status**: ⚠️ 70% Completo

---

### Fase 6: Testes e Qualidade 🔜 **PLANEJADO** (15%)

- [x] Migrar testes relevantes de `tests_legacy/` (parcial)
- [x] Coverage ≥ 69% (meta: 85%)
- [x] 308 testes passando
- [x] CI/CD configurado (GitHub Actions)
- [ ] Adicionar testes de integração workflows
  - [ ] Import → Rules → Post → Report
  - [ ] Create accounts → Add transactions → Generate report
- [ ] Garantir coverage ≥ 80%
- [ ] Performance benchmarks
  - [ ] 50k postings < 2s (relatório)
- [ ] Golden tests para relatórios

**Status**: 🔜 15% Completo

---

### Fase 7: Documentação e Finalização 📋 **PLANEJADO** (0%)

- [x] Atualizar README.md (parcial)
- [x] Criar CLAUDE.md (guia para Claude Code) ✅
- [x] Atualizar plan.md ✅
- [ ] Criar ADR-0002 (Event-Driven Architecture)
- [ ] Criar ADR-0003 (UUID-Integer Conversion)
- [ ] Documentar estrutura de pastas
- [ ] Guia de contribuição
- [ ] Exemplos de uso completos
- [ ] Remover código legado (ou mover para branch)

**Status**: 📋 0% Completo

---

## 🎯 Próximas Prioridades

### **Sprint 1: Cartões & Orçamentos** (1-2 semanas) 🎯 PRÓXIMO
1. **Cartão de Crédito como LIABILITY** (3-4 dias)
   - Tipo de conta LIABILITY
   - BuildCardStatementUseCase
   - PayCardUseCase
   - CLI commands: `fin card build-statement`, `fin card pay`, `fin card list`

2. **Orçamentos** (2-3 dias)
   - Entidade Budget
   - SetBudgetUseCase
   - BudgetReportUseCase
   - CLI commands: `fin budget set|list|report`

### **Sprint 2: TUI** (1 semana)
3. **Terminal UI** (5-7 dias)
   - Dashboard com resumo financeiro
   - Inbox para revisar/postar entries
   - Command Palette (Ctrl+K)
   - Navegação 100% por teclado

### **Sprint 3: NL + ML** (1 semana)
4. **CLI em Linguagem Natural** (3-4 dias)
   - Pydantic AI para parsing NL → Intent
   - `fin ask "<pergunta>"`
   - Preview + confirmação

5. **ML para Classificação** (3-4 dias)
   - TF-IDF + LogisticRegression
   - `fin ml train` e `fin ml suggest`
   - Detecção de outliers

---

## 📊 Métricas de Qualidade

### Testes
- **Total**: 308 testes
- **Passando**: 308 (100%)
- **Coverage**: 69%
- **Meta**: ≥85% coverage

### Camadas
- **Domain**: 82 testes (100% coverage da lógica core)
- **Infrastructure**: 46 testes (repositories + mappers)
- **Application**: 72 testes (use cases com mocks)
- **Integration**: 23 testes (com DB real)
- **CLI**: 85 testes (E2E + unit)

### CI/CD
- ✅ Lint (ruff)
- ✅ Types (mypy)
- ✅ Tests (pytest)
- ✅ Security (safety, bandit)
- ✅ Coverage report
- ✅ Múltiplas versões Python (3.11, 3.12, 3.13)

---

## 🚀 Melhorias Entregues

### Mantido da Versão Legado
- ✅ Modelos SQLAlchemy (migrados para infrastructure)
- ✅ Migrações Alembic (compatíveis)
- ✅ Configuração Pydantic Settings
- ✅ Testes de aceitação
- ✅ Dataset de exemplo

### Novo na Arquitetura Clean
- ✅ Domain entities separadas de ORM
- ✅ Repository pattern explícito
- ✅ UnitOfWork para transações
- ✅ Application services (use cases)
- ✅ Event Bus para auditoria
- ✅ Dependency Injection
- ✅ Structured logging
- ✅ UUID-Integer conversion layer

### Melhorias de Qualidade
- ✅ Testes unitários puros (sem DB)
- ✅ Separação clara de responsabilidades
- ✅ Facilita testar (mock repositories)
- ✅ Preparado para API/TUI sem duplicar código
- ✅ Observabilidade estruturada
- ✅ 308 testes automatizados
- ✅ CI/CD completo

---

## 🔗 Links Úteis

- [plan.md](./plan.md) - Plano geral do projeto
- [CLAUDE.md](./CLAUDE.md) - Guia para Claude Code
- [README.md](./README.md) - Documentação principal
- [ADR-0001: Arquitetura fundacional](./docs/ADRs/ADR-0001.md)

---

## 📝 Notas de Implementação

### Padrões Implementados
1. **Clean Architecture**: 4 camadas isoladas (Domain, Application, Infrastructure, Interfaces)
2. **Repository Pattern**: Abstração de persistência
3. **Unit of Work**: Transações atômicas
4. **Dependency Injection**: Container IoC
5. **Event-Driven**: Domain events + Event Bus
6. **Value Objects**: Money, AccountType (imutáveis)
7. **Factory Pattern**: Account.create(), Transaction.create()
8. **Mapper Pattern**: Domain ↔ ORM conversion
9. **UUID-Integer Conversion**: Performance sem poluir domínio

### Lições Aprendidas
1. **Separar Domain de Infra é fundamental**: Permite testar lógica sem DB
2. **Event Bus facilita auditoria**: Handlers desacoplados
3. **UUID no Domain, Integer no DB**: Melhor dos 2 mundos
4. **Structured logging é essencial**: Debug + produção com mesmo código
5. **DI Container simplifica CLI**: Comandos ficam thin adapters

### Decisões Técnicas Chave
- **SQLite WAL mode**: Performance + segurança
- **Pydantic Settings**: Validação de config
- **Typer + Rich**: CLI moderna e bonita
- **pytest + coverage**: Testes profissionais
- **ruff**: Linting + formatting rápido
- **mypy strict**: Type safety total

---

**Última atualização**: 2025-10-15
**Responsável**: @lgili
**Status**: 70% completo, MVP funcional ✅
