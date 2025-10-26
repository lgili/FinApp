## 1. Reporting Enhancements
- [ ] 1.1 Extend balance-sheet use case to calculate prior-period totals (previous month/ specified)
- [ ] 1.2 Produce comparison deltas (absolute + percentage) in result model

## 2. CLI & Exports
- [ ] 2.1 Add `--compare`, `--export {csv,markdown}`, and `--chart` options to CLI command / alias `fin report balance`
- [ ] 2.2 Implement exporter utilities writing CSV/Markdown files
- [ ] 2.3 Render summary table and optional Rich chart(s) when `--chart` passed

## 3. Quality & Docs
- [ ] 3.1 Unit tests covering comparison math and result model
- [ ] 3.2 CLI integration tests verifying export files and compare output
- [ ] 3.3 Update CLI docs with examples for compare/export/chart usage
