## ADDED Requirements
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
