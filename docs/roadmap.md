# Roadmap

Finlite's journey from a simple CLI to a comprehensive personal finance platform.

---

## ✅ Completed Phases

### Phase 0: Foundation (Week 1) - COMPLETE

**Goal**: Set up project infrastructure and tooling

- [x] Repository structure with backend/docs/tests
- [x] Python packaging with pyproject.toml
- [x] SQLite database with Alembic migrations
- [x] Quality gates: pytest, ruff, mypy
- [x] CI/CD setup with pre-commit hooks

**Delivered**: Solid foundation for iterative development

---

### Phases 1-5: Core Accounting (Weeks 2-6) - COMPLETE

**Goal**: Build core double-entry accounting system

- [x] Account entity with five types (Asset, Liability, Equity, Income, Expense)
- [x] Transaction and Posting entities with balance validation
- [x] Repository pattern with SQLAlchemy
- [x] CLI commands: `accounts create/list/balance`, `transactions create/list`
- [x] Multi-currency support
- [x] Transaction validation (sum to zero, minimum 2 postings)

**Test Coverage**: 175 tests passing

**Delivered**: Functional double-entry accounting system

---

### Phase 6: Event Bus & Domain Events (Week 7) - COMPLETE

**Goal**: Implement event-driven architecture for observability

- [x] Domain events: `AccountCreated`, `TransactionRecorded`, etc.
- [x] Event bus with pub/sub pattern
- [x] Event handlers: `AuditLogHandler`, `ConsoleEventHandler`, `MetricsEventHandler`
- [x] Integration with Use Cases
- [x] Dependency injection with event bus

**Test Coverage**: +11 tests (186 total)

**Delivered**: Event-driven architecture with audit trail

---

### Phase 7: Structured Logging & Documentation (Week 8) - COMPLETE

**Goal**: Production-ready observability and professional documentation

- [x] Structured logging with structlog
- [x] JSON output for production
- [x] Colorized console logs for development
- [x] CLI flags: `--debug`, `--json-logs`
- [x] MkDocs documentation with Material theme
- [x] GitHub Pages deployment
- [x] Professional README with badges

**Test Coverage**: 187 tests passing

**Delivered**: Production-ready observability and comprehensive documentation

---

## 🚧 In Progress

### Phase 8: Bank Statement Import (Weeks 9-10)

**Goal**: Automate transaction entry from bank statements

**Features**:
- [ ] Nubank CSV importer
- [ ] OFX file parser
- [ ] Import batch tracking with deduplication
- [ ] Reconciliation: match imported entries with existing transactions
- [ ] Statement entry states: `imported` → `matched` → `posted`
- [ ] CLI: `fin import nubank <file> --account CHECKING`

**Technical Details**:
- `ImportBatch` entity with SHA256 hash for deduplication
- `StatementEntry` entity with external ID
- Fuzzy matching for reconciliation (date ±3 days, amount ±1%)
- Configuration for column mapping (YAML)

**Success Criteria**:
- Import 100+ transactions from Nubank CSV
- Zero duplicates on re-import
- 95%+ automatic reconciliation rate

---

## 📅 Upcoming Phases

### Phase 9: Rules Engine (Weeks 11-12)

**Goal**: Automate transaction classification

**Features**:
- [ ] Rule definition: IF conditions THEN actions
- [ ] Conditions: regex on payee, amount range, date/time
- [ ] Actions: set account, add tags, set category
- [ ] CLI: `fin rules add/list/apply`
- [ ] Dry-run mode with preview
- [ ] Rule priority and ordering

**Example Rule**:
```yaml
- name: "Groceries at Whole Foods"
  conditions:
    - payee_matches: "(?i)whole foods"
  actions:
    - set_account: "GROCERIES"
    - add_tag: "food"
```

**Success Criteria**:
- 90%+ of transactions auto-classified
- Zero false positives with dry-run
- Sub-second rule application on 1000 transactions

---

### Phase 10: ML-Assisted Classification (Weeks 13-14)

**Goal**: Use machine learning for residual classification

**Features**:
- [ ] TF-IDF vectorization of transaction descriptions
- [ ] Logistic Regression classifier
- [ ] Hybrid approach: Rules first, ML for unknowns
- [ ] CLI: `fin ml train`, `fin ml suggest --threshold 0.8`
- [ ] Confidence scores and explanations
- [ ] Outlier detection with Isolation Forest

**Technical Details**:
- scikit-learn for ML models
- Pickle for model serialization
- Features: payee, description, amount, day of week, time
- Minimum 100 transactions for training

**Success Criteria**:
- 80%+ accuracy on test set
- No suggestions below confidence threshold
- Outlier detection finds anomalies (duplicate charges, unusual amounts)

---

### Phase 11: Reports & Analytics (Weeks 15-16)

**Goal**: Generate financial reports

**Features**:
- [ ] Balance Sheet (Assets = Liabilities + Equity)
- [ ] Income Statement (Revenue - Expenses = Net Income)
- [ ] Cash Flow Statement
- [ ] Budget tracking by category/month
- [ ] Spending trends and visualizations
- [ ] Export to CSV/PDF

**CLI Commands**:
```bash
fin report balance --date 2025-12-31
fin report income-statement --from 2025-01-01 --to 2025-12-31
fin report cashflow --month 2025-10
fin budget set GROCERIES 1200 --month 2025-10
fin budget report --month 2025-10
```

**Success Criteria**:
- Reports match accounting principles
- Sub-second generation for 10k transactions
- Budget variance tracking (actual vs planned)

---

### Phase 12: Investment Tracking (Weeks 17-20)

**Goal**: Track investment portfolio with Brazilian tax rules

**Features**:
- [ ] Security master data (stocks, funds, crypto)
- [ ] Trade recording (buy/sell)
- [ ] Average cost calculation (PM médio BR)
- [ ] Realized P/L with tax reporting
- [ ] Dividends and corporate actions (splits, bonuses)
- [ ] Portfolio valuation with price sync
- [ ] Monthly tax report (IR - Imposto de Renda)

**Entities**:
- `Security`: ticker, name, type, currency
- `Trade`: buy/sell, quantity, price, fees
- `Lot`: tracks cost basis with PM médio
- `Price`: historical prices
- `CorporateAction`: splits, dividends, bonuses

**Brazilian Tax Features**:
- [ ] Monthly P/L calculation
- [ ] Loss carryforward
- [ ] Exemption for sales <20k/month (stocks)
- [ ] DARF generation helpers

**Success Criteria**:
- Accurate PM médio calculation (error ≤ R$ 0.01)
- Tax report matches broker statements
- Handle complex scenarios (splits, bonuses, intraday)

---

### Phase 13: Terminal UI (TUI) (Weeks 21-23)

**Goal**: Rich terminal interface for interactive workflows

**Features**:
- [ ] Dashboard with key metrics
- [ ] Inbox for imported transactions
- [ ] Transaction browser with search
- [ ] Rule editor
- [ ] Command Palette (Ctrl+K) with fuzzy search
- [ ] Real-time updates

**Technology**:
- Textual framework for TUI
- Rich for formatting
- Command Palette supports natural language

**Screens**:
```
┌──────────────────────────────────────────┐
│ Dashboard                                │
│ ┌────────────┬────────────┬──────────┐  │
│ │ Assets     │ Income     │ Expenses │  │
│ │ $10,000    │ $5,000     │ $3,000   │  │
│ └────────────┴────────────┴──────────┘  │
│                                          │
│ Recent Transactions                      │
│ ┌──────────────────────────────────────┐│
│ │ 10/12  Groceries      -$150  [Edit] ││
│ │ 10/11  Salary        +$3000  [View] ││
│ └──────────────────────────────────────┘│
└──────────────────────────────────────────┘
```

**Success Criteria**:
- Responsive UI (60 FPS)
- Keyboard-first navigation
- Works on 80x24 terminal

---

### Phase 14: Natural Language CLI (Weeks 24-25)

**Goal**: AI-powered natural language interface

**Features**:
- [ ] Pydantic AI for intent parsing
- [ ] Structured output with validation
- [ ] Command preview before execution
- [ ] Confirmation for destructive actions
- [ ] Local LLM support (llama.cpp)

**Examples**:
```bash
fin ask "import nubank.csv and auto-classify"
# Preview:
#   fin import nubank nubank.csv --account CHECKING
#   fin rules apply --auto
#   fin post pending --auto
# Execute? [y/N]: y

fin ask "how much did I spend on groceries last month?"
# → fin report expenses --category GROCERIES --month 2025-09

fin ask "transfer 500 from checking to savings"
# Preview:
#   fin transactions create -d "Transfer to savings"
#   Posting 1: SAVINGS, 500
#   Posting 2: CHECKING, -500
# Execute? [y/N]: y
```

**Technology**:
- Pydantic AI for agent framework
- Intent schemas with Pydantic models
- Tools for CLI commands
- Fallback to rule-based parsing

**Success Criteria**:
- 90%+ intent recognition accuracy
- Zero false executions (dry-run validation)
- Works 100% offline with local models

---

### Phase 15: Web UI (Optional) (Weeks 26-30)

**Goal**: Modern web interface for visualization

**Features**:
- [ ] Vue 3 + Vite + Tailwind/DaisyUI
- [ ] FastAPI backend (read-only first)
- [ ] Dashboard with charts (ECharts)
- [ ] Transaction browser
- [ ] Budget tracking
- [ ] Investment portfolio view

**Architecture**:
- FastAPI exposes existing use cases
- JWT authentication (local file-based)
- SPA with client-side routing
- WebSocket for real-time updates (optional)

**Success Criteria**:
- Works offline (local-first)
- Responsive design (mobile + desktop)
- No rewrite of core logic (reuse use cases)

---

## 🎯 Long-Term Vision

### Multi-User & Sync (Future)

- [ ] User accounts and permissions
- [ ] Cloud sync (optional, encrypted)
- [ ] Multi-device support
- [ ] Sharing and collaboration

### Advanced Features (Future)

- [ ] Forecasting and predictions
- [ ] Goal tracking (savings goals)
- [ ] Debt payoff calculator
- [ ] Retirement planning
- [ ] Tax optimization suggestions

### Integration (Future)

- [ ] Plaid/Belvo for automatic bank sync
- [ ] Open Banking APIs (Brazil)
- [ ] Export to accounting software
- [ ] Mobile app (React Native)

---

## 📊 Project Metrics

### Current Status (Phase 7 Complete)

- **Lines of Code**: ~8,000
- **Test Coverage**: 187 tests (163 unit + 24 integration)
- **Type Coverage**: 100% (mypy strict)
- **Documentation Pages**: 12+
- **CLI Commands**: 6 main commands
- **Supported Account Types**: 5
- **Supported Currencies**: Unlimited

### Goals by Phase 15

- **Lines of Code**: ~30,000
- **Test Coverage**: 500+ tests
- **Documentation Pages**: 50+
- **CLI Commands**: 20+
- **Features**: Import, Rules, ML, Reports, Investments, TUI, NL

---

## 🤝 Contributing

Want to help build Finlite? Check out our [Contributing Guide](development/contributing.md)!

**Priority areas**:
- 🐛 Bug fixes
- 📖 Documentation improvements
- 🧪 Test coverage
- 🎨 UX improvements
- ✨ Feature implementations

---

## 📝 Release Schedule

- **v0.1.0** (Current): Core accounting + Events + Logging
- **v0.2.0** (Q1 2026): Import + Rules + ML
- **v0.3.0** (Q2 2026): Reports + Budgets
- **v0.4.0** (Q3 2026): Investments + Tax
- **v1.0.0** (Q4 2026): TUI + NL + Stable API

---

## 📞 Feedback

Have ideas for the roadmap? We'd love to hear!

- 💬 [Discussions](https://github.com/lgili/finapp/discussions)
- 💡 [Feature Requests](https://github.com/lgili/finapp/issues/new?labels=enhancement)
- 🐛 [Bug Reports](https://github.com/lgili/finapp/issues/new?labels=bug)

---

*Last updated: October 12, 2025*
