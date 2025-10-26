## ADDED Requirements
### Requirement: Define Monthly Budget
The system MUST allow configuring a budget amount for a category and period.

#### Scenario: Set groceries budget
- **WHEN** the user runs `fin budget set "Expenses:Groceries" 1200 --month 2025-10`
- **THEN** the budget is stored with amount 1200 for October 2025
- **AND** the CLI confirms the configured value

### Requirement: Budget vs Actual Report
The system MUST compare actual spending with the configured budget and highlight variance.

#### Scenario: Report monthly variance
- **GIVEN** actual spending of 1.350 in October for groceries
- **WHEN** the user runs `fin budget report --month 2025-10`
- **THEN** the CLI shows planned 1.200, actual 1.350, variance +12.5%
- **AND** overspend entries are highlighted

### Requirement: Budget Rollover
The system MUST optionally carry unused budget amounts to the next period when rollover is enabled.

#### Scenario: Rollover unused funds
- **GIVEN** a budget with rollover enabled and 200 unused in October
- **WHEN** the November budget activates
- **THEN** the available amount includes the 200 carried over
- **AND** the report indicates the rollover contribution
