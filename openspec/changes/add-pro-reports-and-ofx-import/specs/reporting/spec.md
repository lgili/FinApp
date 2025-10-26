## ADDED Requirements
### Requirement: Balance Sheet Report
The system MUST provide a CLI balance sheet report with period comparison and export formats.

#### Scenario: Generate balance sheet with comparison
- **WHEN** the user runs `fin report balance --date 2025-10-31 --compare previous`
- **THEN** the CLI displays Assets, Liabilities, and Equity totals with deltas vs the previous period
- **AND** the user can export the result as CSV, Markdown, or PDF

### Requirement: Income Statement Report
The system MUST provide an income statement report with YoY comparison.

#### Scenario: Generate income statement
- **WHEN** the user runs `fin report income-statement --from 2025-10-01 --to 2025-10-31 --compare yoy`
- **THEN** the CLI outputs Revenues, Expenses, and Net Income with YoY percentages
- **AND** charts are available when `--chart` is passed

### Requirement: Import OFX Statements
The system MUST import OFX files into statement entries compatible with existing workflows.

#### Scenario: OFX import command
- **WHEN** the user runs `fin import ofx extrato.ofx`
- **THEN** the CLI reports how many transactions were imported
- **AND** the entries include bank metadata and are ready for rules/posting pipelines
