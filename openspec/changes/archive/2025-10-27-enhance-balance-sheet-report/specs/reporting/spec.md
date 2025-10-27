## MODIFIED Requirements
### Requirement: CLI Balance Sheet Report
The system MUST provide a CLI command that summarizes account balances by type (Assets, Liabilities, Equity) as of a specified effective date, defaulting to today, and offer period comparison & export capabilities.

#### Scenario: Compare against previous period
- **WHEN** the user runs `fin report balance-sheet --date 2025-10-31 --compare previous`
- **THEN** the CLI displays Assets, Liabilities, Equity totals alongside deltas versus 2025-09-30
- **AND** the net worth row includes absolute and percentage change indicators

#### Scenario: Export balance sheet to CSV
- **WHEN** the user runs `fin report balance-sheet --date 2025-10-31 --export csv --output balance-oct.csv`
- **THEN** a file `balance-oct.csv` is created containing totals per section and comparison figures
- **AND** the CLI confirms the export location

#### Scenario: Render chart for balance sheet
- **WHEN** the user runs `fin report balance --chart`
- **THEN** the CLI renders a Rich chart representing Assets vs Liabilities vs Equity
- **AND** textual summary remains visible for accessibility
