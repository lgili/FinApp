## 1. Domain & Persistence
- [ ] 1.1 Extend account model to support credit-card metadata (closing/due dates, issuer)
- [ ] 1.2 Add repositories/migrations for credit card statements and installments

## 2. Application Use Cases
- [ ] 2.1 Implement `BuildCardStatementUseCase` composing purchases within a billing cycle
- [ ] 2.2 Implement `PayCardUseCase` to transfer funds from asset accounts and mark statement as paid
- [ ] 2.3 Provide installment handling (split purchases over multiple cycles)

## 3. CLI & UX
- [ ] 3.1 Add `fin card build-statement`, `fin card pay`, and `fin card list` commands
- [ ] 3.2 Render statement summaries with totals, installments, and due dates using Rich tables
- [ ] 3.3 Update docs with walkthroughs for importing, reconciling, and paying cards

## 4. Quality
- [ ] 4.1 Unit tests for statement cycle calculations and payoff edge cases
- [ ] 4.2 Integration tests covering CLI workflows over sample card data
- [ ] 4.3 Ensure migrations and repositories have regression coverage
