# Reports

## Purpose
Specify the reporting and export capabilities that translate ledger data into actionable insights and external formats for Finlite users.

## Requirements
### Requirement: Cashflow Report
The system MUST generate a cashflow report aggregating income and expenses over a specified period.

#### Scenario: Cashflow report via CLI
- **GIVEN** transactions posted within October 2025
- **WHEN** the user runs `fin report cashflow --from 2025-10-01 --to 2025-10-31`
- **THEN** the CLI outputs totals grouped by income and expense categories
- **AND** the report highlights net cashflow for the requested period

### Requirement: Export Beancount
The system MUST export ledger data to Beancount format through the CLI.

#### Scenario: Export command produces file
- **GIVEN** an existing ledger with accounts and transactions
- **WHEN** the user runs `fin export beancount output.beancount`
- **THEN** a file named `output.beancount` is created
- **AND** the file contains header metadata and transaction entries compatible with Beancount
