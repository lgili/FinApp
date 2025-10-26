## ADDED Requirements
### Requirement: Income Statement Report
The system MUST provide an income statement report that summarizes revenues, expenses, and net income for a configurable period with comparison options.

#### Scenario: Generate income statement
- **WHEN** the user runs `fin report income-statement --from 2025-10-01 --to 2025-10-31`
- **THEN** the CLI outputs totals for Revenues, Expenses, and Net Income grouped by account/category
- **AND** net income is highlighted with appropriate color coding

#### Scenario: Compare YoY performance
- **WHEN** the user runs `fin report income-statement --from 2025-10-01 --to 2025-10-31 --compare yoy`
- **THEN** the CLI shows percentage and absolute deltas compared to the same period in 2024
- **AND** the summary indicates whether net income increased or decreased

#### Scenario: Export income statement
- **WHEN** the user runs `fin report income-statement --from 2025-10-01 --to 2025-10-31 --export markdown --output income-oct.md`
- **THEN** a Markdown file with the tabular report and comparison metrics is generated
- **AND** the CLI confirms the export path
