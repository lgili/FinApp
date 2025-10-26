## 1. Parser
- [x] 1.1 Evaluate lightweight OFX parsing library or implement streaming parser
- [x] 1.2 Normalize transactions (date, amount, memo, external id, account)

## 2. Use Case & CLI
- [x] 2.1 Implement `ImportOFXUseCase` mapping parsed items to `StatementEntry`
- [x] 2.2 Add CLI command `fin import ofx <file>` with bank detection and summary output
- [x] 2.3 Handle duplicates via checksum/external id logic

## 3. Quality & Docs
- [x] 3.1 Fixture OFX files + integration tests for import pipeline
- [x] 3.2 Unit tests for parser edge cases (multi-currency, pending transactions)
- [x] 3.3 Update docs with OFX instructions, supported banks, and troubleshooting
