# 📋 Plano de Desenvolvimento — Finlite

**Última atualização**: 2025-10-15
**Status Atual**: MVP Contábil Funcional ✅ | Próximo: Cartões & Orçamentos

---

## 🎯 Visão do Projeto

**finlite** é um app de finanças pessoais **local-first** com:
- ✅ Contabilidade de dupla entrada (double-entry bookkeeping)
- ✅ Ingestão bancária automatizada (Nubank CSV, OFX em breve)
- ✅ Regras de classificação + ML local para sugestões
- ✅ Relatórios gerenciais (cashflow, balanço, DRE)
- 🔜 Módulo de investimentos (trades, P/L, proventos, IR mensal)
- 🔜 TUI (Terminal UI) interativo + CLI em linguagem natural

**Não-objetivos iniciais**: nuvem, multiusuário, sync (podem vir depois sem quebrar o core)

---

## ✅ O Que Já Está Pronto (Status: 2025-10-15)

### **Arquitetura Limpa & Fundação** ✅
- ✅ Clean Architecture com 4 camadas (Domain, Application, Infrastructure, Interfaces)
- ✅ Domain-Driven Design (Entities, Value Objects, Repository Pattern)
- ✅ Dependency Injection com `dependency-injector`
- ✅ Event Bus (InMemoryEventBus) + Domain Events
- ✅ Structured Logging com `structlog` (JSON logs + debug colorido)
- ✅ Unit of Work pattern para transações atômicas
- ✅ UUID-Integer conversion layer (Domain usa UUID, DB usa integers)

### **Domain Layer** ✅ (82 testes)
- ✅ **Entities**: Account, Transaction, Posting, ImportBatch, StatementEntry
- ✅ **Value Objects**: Money (Decimal + currency), AccountType enum
- ✅ **Repository Interfaces**: IAccountRepository, ITransactionRepository, IImportBatchRepository, IStatementEntryRepository
- ✅ **Domain Exceptions**: UnbalancedTransactionError, AccountNotFoundError, DuplicateImportError, etc.
- ✅ **Validações**: Transações balanceadas (soma zero), contas hierárquicas, moedas validadas (ISO 4217)

### **Infrastructure Layer** ✅ (46 testes)
- ✅ SQLite com WAL mode + foreign keys
- ✅ SQLAlchemy models + Alembic migrations
- ✅ Repository implementations (SqlAlchemyAccountRepository, SqlAlchemyTransactionRepository, etc.)
- ✅ Mappers (Domain ↔ ORM) com UUID-Integer conversion
- ✅ Event handlers (AuditLogHandler, MetricsEventHandler)
- ✅ Pydantic Settings para configuração

### **Application Layer - Use Cases** ✅ (72 testes)
- ✅ **Contas**: CreateAccount, ListAccounts, GetAccountBalance
- ✅ **Transações**: RecordTransaction, ListTransactions
- ✅ **Ingestão**: ImportNubankStatement
- ✅ **Classificação**: ApplyRulesUseCase (regras com regex, filtros de valor/tempo)
- ✅ **Postagem**: PostPendingEntriesUseCase (converte entries → transações balanceadas)
- ✅ **Relatórios**: GenerateCashflowReportUseCase (agregação por período e categoria)
- ✅ **Exportação**: ExportBeancountUseCase (export para formato Beancount)

### **CLI (Interface Layer)** ✅
- ✅ Typer + Rich para output formatado
- ✅ Comandos disponíveis:
  ```bash
  fin accounts create|list|balance
  fin transactions create|list
  fin import nubank <csv>
  fin rules apply [--dry-run] [--batch <id>]
  fin post pending [--dry-run] [--source <account>]
  fin report cashflow [--from DATE] [--to DATE]
  fin export beancount <output.beancount>
  ```
- ✅ Global options: `--debug`, `--json-logs`
- ✅ DI Container integrado
- ✅ Error handling com mensagens claras

### **Testes & Qualidade** ✅
- ✅ **308 testes passando** (100% de sucesso)
- ✅ Cobertura de código: 69%
- ✅ CI/CD com GitHub Actions (lint, tipos, testes, segurança)
- ✅ Ruff (linting + formatting) + mypy (type checking)
- ✅ Pre-commit hooks configurados

### **Workflow Completo Funcional** ✅
```bash
# 1. Importar extrato bancário
fin import nubank extrato.csv

# 2. Aplicar regras de classificação
fin rules apply

# 3. Postar entries como transações
fin post pending

# 4. Gerar relatório de fluxo de caixa
fin report cashflow --from 2025-10-01 --to 2025-10-31

# 5. Exportar para Beancount
fin export beancount ~/ledger.beancount
```

---

## 🚀 Roadmap - Próximas Fases

### **Fase 1: Cartões & Orçamentos** (1-2 semanas) 🎯 PRÓXIMO
**Objetivo**: Tornar o app imediatamente útil para 90% das pessoas

#### 1.1 Cartão de Crédito como LIABILITY (3-4 dias)
- [ ] Criar tipo de conta `LIABILITY` para cartões
- [ ] Implementar `BuildCardStatementUseCase`:
  ```bash
  fin card build-statement --from 2025-10-01 --to 2025-10-31 --card Nubank
  ```
- [ ] Implementar `PayCardUseCase` (transferência Assets → Liabilities):
  ```bash
  fin card pay --amount 5000 --from Assets:Bank:Checking --card Liabilities:CreditCard:Nubank
  ```
- [ ] CLI commands: `fin card build-statement`, `fin card pay`, `fin card list`
- [ ] Testes: fechamento de fatura, quitação, parcelas

**Entregáveis**:
- ✅ Cartões como Liabilities no balanço
- ✅ Fechamento de fatura automático
- ✅ Lançamento de pagamento

#### 1.2 Orçamentos (2-3 dias)
- [ ] Criar entidade `Budget` (categoria, valor, período)
- [ ] Implementar `SetBudgetUseCase`:
  ```bash
  fin budget set "Expenses:Groceries" 1200 --month 2025-10
  ```
- [ ] Implementar `BudgetReportUseCase` (real vs orçado):
  ```bash
  fin budget report --month 2025-10
  ```
- [ ] Suporte a rollover (orçamento não gasto acumula)
- [ ] Alertas de estouro de orçamento
- [ ] CLI commands: `fin budget set|list|report`
- [ ] Testes: definição, comparação, rollover

**Entregáveis**:
- ✅ Definir orçamento por categoria/mês
- ✅ Comparar real vs orçado com % de utilização
- ✅ Alertas visuais de estouro

**Critério de Aceite Fase 1**:
- Usuário pode importar fatura do cartão, revisar e pagar
- Usuário define orçamento e vê comparativo mensal
- Testes cobrindo cenários reais (parcelas, estouro, rollover)

---

### **Fase 2: TUI (Terminal UI)** (1 semana)
**Objetivo**: Experiência "desktop app" no terminal

#### 2.1 Dashboard & Inbox (3-4 dias)
- [ ] Configurar Textual framework
- [ ] Criar layout base: Header, Sidebar, Content, Footer
- [ ] Dashboard:
  - Resumo financeiro (receitas, despesas, saldo)
  - Gráficos com Rich (sparklines, barras)
  - Top 5 categorias do mês
- [ ] Inbox (entries importados):
  - Listar entries com status (IMPORTED/MATCHED/POSTED)
  - Navegação por teclado (↑↓ para navegar, Enter para abrir)
  - Ações: A=aceitar/postar, E=editar, D=deletar, R=aplicar regras
  - Filtros: /search, status, valor, data

#### 2.2 Command Palette (2-3 dias)
- [ ] Implementar Command Palette (Ctrl+K)
- [ ] Fuzzy search com `rapidfuzz`
- [ ] Comandos disponíveis:
  - "Import Nubank CSV..."
  - "Apply rules to imported entries"
  - "Post pending entries"
  - "Cashflow report for October"
  - "Export to Beancount..."
- [ ] Preview de comandos antes de executar
- [ ] Histórico de comandos recentes

#### 2.3 Outras Telas
- [ ] Ledger (lista de transações com filtros)
- [ ] Accounts (árvore hierárquica de contas)
- [ ] Reports (visualização de relatórios)
- [ ] Rules (gerenciar regras de classificação)

**Entregáveis**:
- ✅ TUI funcional com Dashboard + Inbox
- ✅ Command Palette com fuzzy search
- ✅ Navegação 100% por teclado
- ✅ Experiência fluida para revisar/postar dezenas de entries

**Critério de Aceite Fase 2**:
- Usuário abre `fin tui` e navega sem usar mouse
- Inbox permite aceitar/postar entries rapidamente
- Command Palette encontra comandos rapidamente

---

### **Fase 3: NL + ML Local** (1 semana)
**Objetivo**: Reduzir trabalho manual em 50-70%

#### 3.1 CLI em Linguagem Natural (3-4 dias)
- [ ] Integrar Pydantic AI para parsing NL → Intent
- [ ] Criar schemas de Intent (Pydantic):
  - `ImportFileIntent`
  - `ReportCashflowIntent`
  - `PostPendingIntent`
  - `CreateRuleIntent`
  - `ListTransactionsIntent`
- [ ] Implementar `fin ask "<pergunta>"`:
  ```bash
  fin ask "importe extrato.csv do nubank e lance tudo"
  fin ask "quanto gastei com mercado em setembro?"
  fin ask "crie uma regra para Netflix -> Entretenimento"
  ```
- [ ] Preview de comandos antes de executar
- [ ] Confirmação para ações destrutivas
- [ ] Flag `--explain` para mostrar raciocínio
- [ ] Fallback: gramáticas/regex para intents comuns (não precisa LLM sempre)
- [ ] Suporte a LLM local (llama.cpp) ou cloud (OpenAI/Anthropic)

#### 3.2 ML para Classificação Automática (3-4 dias)
- [ ] Implementar `TrainMLModelUseCase`:
  ```bash
  fin ml train
  ```
- [ ] Pipeline: TF-IDF + LogisticRegression (scikit-learn)
- [ ] Serializar modelo (joblib/pickle)
- [ ] Implementar `SuggestAccountUseCase` (ML-based):
  ```bash
  fin ml suggest --threshold 0.8
  ```
- [ ] Híbrido: Regras > ML (ML só no residual)
- [ ] Métricas: acurácia, precision, recall
- [ ] Relatório de performance: `fin ml report`

#### 3.3 Detecção de Outliers (1-2 dias)
- [ ] Implementar `DetectOutliersUseCase`:
  ```bash
  fin detect outliers --month 2025-10
  ```
- [ ] IsolationForest para detectar anomalias
- [ ] Alertas: "Você gastou R$ 500 com mercado, 3x acima da média"

**Entregáveis**:
- ✅ `fin ask` funcional com preview e confirmação
- ✅ ML treinado automaticamente com histórico
- ✅ Sugestões de conta com score de confiança
- ✅ Detector de anomalias

**Critério de Aceite Fase 3**:
- Usuário pode usar linguagem natural para comandos comuns
- ML sugere conta correta em ≥80% dos casos (após treino)
- Outliers detectados corretamente

---

### **Fase 4: Relatórios Pro & OFX** (1 semana)

#### 4.1 Relatórios Profissionais (2-3 dias)
- [ ] Implementar `BalanceSheetUseCase`:
  ```bash
  fin report balance --date 2025-10-31
  ```
  - Ativos, Passivos, Patrimônio Líquido
  - Comparação com período anterior
- [ ] Implementar `IncomeStatementUseCase`:
  ```bash
  fin report income-statement --from 2025-10-01 --to 2025-10-31
  ```
  - Receitas, Despesas, Resultado
  - Comparação YoY (Year over Year)
- [ ] Export para CSV/Markdown/PDF
- [ ] Gráficos (Rich/matplotlib) opcionais

#### 4.2 Import OFX (2-3 dias)
- [ ] Parser OFX (XML)
- [ ] Implementar `ImportOFXUseCase`:
  ```bash
  fin import ofx extrato.ofx
  ```
- [ ] Mapeamento OFX → StatementEntry
- [ ] Suporte a múltiplos bancos
- [ ] Testes com arquivos OFX reais

**Entregáveis**:
- ✅ Balanço Patrimonial
- ✅ DRE (Demonstração de Resultados)
- ✅ Import OFX funcionando

**Critério de Aceite Fase 4**:
- Relatórios batem com valores esperados
- OFX de diferentes bancos importa corretamente

---

### **Fase 5: Investimentos - Básico** (2 semanas)

#### 5.1 Trades & Lotes (1 semana)
- [ ] Criar entidades: `Security`, `Trade`, `Lot`
- [ ] Implementar cálculo de PM (Preço Médio) brasileiro
- [ ] Implementar `ImportTradesUseCase`:
  ```bash
  fin inv import-trades trades.csv
  ```
- [ ] Implementar `HoldingsReportUseCase`:
  ```bash
  fin inv holdings
  ```
- [ ] Implementar `PnLReportUseCase`:
  ```bash
  fin inv pnl --from 2025-01-01 --to 2025-12-31
  ```

#### 5.2 Proventos & Preços (1 semana)
- [ ] Criar entidade `Dividend` (dividendos, JCP)
- [ ] Implementar `ImportDividendsUseCase`:
  ```bash
  fin inv dividends import dividends.csv
  ```
- [ ] Criar entidade `Price` (cotações)
- [ ] Implementar `SyncPricesUseCase`:
  ```bash
  fin inv prices sync --source csv:./precos.csv
  ```
- [ ] Marcação a mercado
- [ ] Yield on Cost (YoC)

**Entregáveis**:
- ✅ Controle de carteira de ações/FIIs
- ✅ P/L realizado
- ✅ Proventos recebidos
- ✅ Marcação a mercado

**Critério de Aceite Fase 5**:
- PM calculado corretamente (casos clássicos)
- P/L realizado bate com referência
- Proventos contabilizados corretamente

---

### **Fase 6: IR Mensal** (1 semana)

- [ ] Implementar `MonthlyTaxReportUseCase`:
  ```bash
  fin tax monthly --month 2025-10 --export csv
  ```
- [ ] Cálculo de IR mensal (PM médio)
- [ ] Compensação de prejuízos
- [ ] Isenção (vendas ≤ R$ 20k/mês)
- [ ] Geração de base para DARF

**Entregáveis**:
- ✅ Relatório de IR mensal
- ✅ Base de cálculo para DARF

**Critério de Aceite Fase 6**:
- Cálculo de IR bate com casos de referência BR

---

### **Fase 7: Polimento & Qualidade** (1 semana)

- [ ] Aumentar cobertura de testes para ≥85%
- [ ] Testes de integração end-to-end:
  - Import → Rules → Post → Report → Export
- [ ] Performance benchmarks:
  - 50k postings → relatório < 2s
- [ ] Golden tests para relatórios
- [ ] Documentação completa (README, ADRs, guias)
- [ ] Remover código legado

---

### **Fase 8 (Opcional): Web UI** (2-3 semanas)

- [ ] FastAPI backend (read-only primeiro)
- [ ] Endpoints: Dashboard, Inbox, Ledger, Reports, Investimentos
- [ ] Auth local (token no arquivo)
- [ ] Frontend Vue 3 + Vite + Tailwind/DaisyUI:
  - Dashboard com gráficos (ECharts/Chart.js)
  - Inbox (aceitar/editar/postar)
  - Transações com busca avançada
  - Regras (lista/validação)
  - Investimentos (posições, P/L, proventos)

**Entregáveis**:
- ✅ UI web bonita
- ✅ Paridade de leitura com CLI/TUI

---

## 📊 Progresso Geral

```
✅ Fase 0: Fundação          [████████████] 100%
✅ Fase 1: Domain            [████████████] 100%
✅ Fase 2: Infrastructure    [████████████] 100%
✅ Fase 3: Event Bus/Logs    [████████████] 100%
✅ Fase 4: Use Cases Core    [██████████░░]  85%
✅ Fase 5: CLI Básica        [████████░░░░]  70%
⬜ Fase 6: Cartões/Orçamento [░░░░░░░░░░░░]   0% 🎯 PRÓXIMO
⬜ Fase 7: TUI               [░░░░░░░░░░░░]   0%
⬜ Fase 8: NL + ML           [░░░░░░░░░░░░]   0%
⬜ Fase 9: Relatórios Pro    [░░░░░░░░░░░░]   0%
⬜ Fase 10: Investimentos    [░░░░░░░░░░░░]   0%
⬜ Fase 11: IR Mensal        [░░░░░░░░░░░░]   0%
⬜ Fase 12: Web UI           [░░░░░░░░░░░░]   0% (opcional)

Status Geral: ~35% completo
MVP Básico: ~85% completo ✅
```

---

## 🎯 Decisões de Arquitetura (ADRs)

### ADR-0001: Clean Architecture
- **Status**: Aceito ✅
- **Contexto**: Necessidade de separar lógica de negócio de detalhes técnicos
- **Decisão**: Adotar Clean Architecture com 4 camadas
- **Consequências**: Código testável, manutenível, preparado para múltiplas interfaces

### ADR-0002: Event-Driven Architecture
- **Status**: Aceito ✅
- **Contexto**: Necessidade de auditoria e observabilidade
- **Decisão**: Event Bus para domain events (AccountCreated, TransactionRecorded, etc.)
- **Consequências**: Desacoplamento, fácil adicionar novos handlers

### ADR-0003: UUID vs Integer IDs
- **Status**: Aceito ✅
- **Contexto**: Domain precisa de UUIDs, DB performa melhor com integers
- **Decisão**: UUID-Integer conversion layer na infraestrutura
- **Consequências**: Melhor performance sem poluir domínio

### ADR-0004: SQLite como DB Principal
- **Status**: Aceito ✅
- **Contexto**: Local-first, sem necessidade de servidor
- **Decisão**: SQLite com WAL mode
- **Consequências**: Simples, portável, performático para uso pessoal

---

## 📚 Stack Tecnológica

### Core
- **Linguagem**: Python 3.11+
- **DB**: SQLite (WAL mode) + Alembic
- **ORM**: SQLAlchemy 2.0
- **DI**: dependency-injector
- **Validação**: Pydantic

### CLI/TUI
- **CLI**: Typer + Rich
- **TUI**: Textual (planejado)

### Testes & Qualidade
- **Testes**: pytest + pytest-cov + pytest-mock
- **Linting**: ruff (lint + format)
- **Tipos**: mypy
- **CI/CD**: GitHub Actions
- **Pre-commit**: ruff + mypy

### ML & NL (planejado)
- **ML**: scikit-learn (TF-IDF + LogisticRegression)
- **NL**: Pydantic AI + llama.cpp (local) ou OpenAI/Anthropic
- **Outliers**: IsolationForest

### Web (opcional)
- **Backend**: FastAPI
- **Frontend**: Vue 3 + Vite + Tailwind/DaisyUI
- **Gráficos**: ECharts ou Chart.js

---

## 🔗 Links Úteis

- [MIGRATION_ROADMAP.md](./MIGRATION_ROADMAP.md) - Roadmap detalhado de migração
- [README.md](./README.md) - Documentação principal
- [CLAUDE.md](./CLAUDE.md) - Guia para Claude Code
- [ADRs](./docs/ADRs/) - Architecture Decision Records

---

## 📝 Notas de Desenvolvimento

### Princípios
1. **Local-first**: Tudo funciona offline, SQLite como fonte da verdade
2. **Testes sempre**: Não mergear sem testes passando
3. **Commits atômicos**: 1 commit = 1 feature/fix pequeno
4. **Clean Architecture**: Domain nunca depende de infra
5. **Type safety**: mypy strict mode
6. **Auditoria**: Todo evento importante é logado

### Workflow de Desenvolvimento
```bash
# 1. Criar branch
git checkout -b feat/card-liability

# 2. Implementar com testes
pytest --cov

# 3. Lint + tipos
ruff check . && ruff format . && mypy .

# 4. Commit
git commit -m "feat(domain): add LIABILITY account type for credit cards"

# 5. Push + PR
git push origin feat/card-liability
```

### Convenções de Commit
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `refactor:` - Refatoração sem mudança de comportamento
- `test:` - Adição/modificação de testes
- `docs:` - Documentação
- `chore:` - Build, CI, dependências

---

**Responsável**: @lgili
**Início**: 2025-10-11
**Última revisão**: 2025-10-15
