## 1. Domain & Persistence
- [ ] 1.1 Create `Budget` entity with period, category, and rollover behavior
- [ ] 1.2 Add repositories and migrations for budgets and history snapshots

## 2. Application Use Cases
- [ ] 2.1 Implement `SetBudgetUseCase` and `ListBudgetsUseCase`
- [ ] 2.2 Implement `BudgetReportUseCase` summarizing actual vs planned amounts
- [ ] 2.3 Support rollover logic for unused budgets

## 3. CLI & Alerts
- [ ] 3.1 Add `fin budget set|list|report` commands
- [ ] 3.2 Display variance percentages and highlight overspend conditions
- [ ] 3.3 Emit alerts (CLI warnings/logs) when a budget exceeds configured threshold

## 4. Quality
- [ ] 4.1 Unit tests for budget calculations, rollover, and variance
- [ ] 4.2 Integration tests validating CLI flows over sample ledger data
- [ ] 4.3 Update docs/tutorials with budgeting walkthrough
