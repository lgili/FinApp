## 1. Parser
- [ ] 1.1 Evaluate lightweight OFX parsing library or implement streaming parser
- [ ] 1.2 Normalize transactions (date, amount, memo, external id, account)

## 2. Use Case & CLI
- [ ] 2.1 Implement `ImportOFXUseCase` mapping parsed items to `StatementEntry`
- [ ] 2.2 Add CLI command `fin import ofx <file>` with bank detection and summary output
- [ ] 2.3 Handle duplicates via checksum/external id logic

## 3. Quality & Docs
- [ ] 3.1 Fixture OFX files + integration tests for import pipeline
- [ ] 3.2 Unit tests for parser edge cases (multi-currency, pending transactions)
- [ ] 3.3 Update docs with OFX instructions, supported banks, and troubleshooting
