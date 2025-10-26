## 1. Advanced Reports
- [ ] 1.1 Implement `BalanceSheetUseCase` with period comparison logic
- [ ] 1.2 Implement `IncomeStatementUseCase` with YoY comparison
- [ ] 1.3 Add CLI commands `fin report balance` and `fin report income-statement`
- [ ] 1.4 Support export options (CSV, Markdown, PDF) and optional charts

## 2. OFX Import
- [ ] 2.1 Build OFX parser capable of handling multiple bank variants
- [ ] 2.2 Implement `ImportOFXUseCase` with CLI command `fin import ofx`
- [ ] 2.3 Map OFX transactions into `StatementEntry` records with metadata

## 3. Quality & Docs
- [ ] 3.1 Unit tests for report aggregation and formatting
- [ ] 3.2 Integration tests for OFX ingestion using fixture files
- [ ] 3.3 Update CLI guide and docs with report/OFX usage examples
