# reporting Specification

## Purpose
Describe reporting features delivered via CLI, covering balance sheet snapshots and monthly tax summaries that help users audit financial health and compliance.
## Requirements
### Requirement: CLI Balance Sheet Report
The system MUST provide a CLI command that summarizes account balances by type (Assets, Liabilities, Equity) as of a specified effective date, defaulting to today.

#### Scenario: View balance sheet for today
- **GIVEN** there are posted transactions affecting at least one asset and one liability account
- **WHEN** the user runs `fin reports balance-sheet`
- **THEN** the CLI outputs a table with totals for Assets, Liabilities, and Equity
- **AND** the table includes a Net Worth row showing Assets minus Liabilities

#### Scenario: View balance sheet for a past date
- **GIVEN** historical transactions exist before and after 2024-01-01
- **WHEN** the user runs `fin reports balance-sheet --at 2024-01-01`
- **THEN** balances are calculated using only postings dated on or before 2024-01-01
- **AND** the CLI labels the report with the effective date

### Requirement: Monthly Capital Gains Tax Report
The system MUST generate a monthly Brazilian IR summary that applies the R$20.000 sales exemption, loss carryover, dividends/JCP aggregation, and DARF calculation.

#### Scenario: Generate monthly tax report
- **WHEN** the user runs `fin tax monthly --month 2025-10`
- **THEN** the CLI outputs total sales, exempt sales, taxable gains, losses carried in/out, DARF rate and payable amount
- **AND** the user may export the summary with `--export csv`

#### Scenario: Apply loss carryover
- **GIVEN** trades tagged with `tax:loss=2000` in September and `tax:gain=5000` in October
- **WHEN** generating `fin tax monthly --month 2025-10`
- **THEN** the taxable base is reduced by the R$ 2.000 carryover before calculating DARF
- **AND** the CLI highlights the carry-in, applied, and carry-out loss amounts

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

