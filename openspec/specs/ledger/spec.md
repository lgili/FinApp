# Ledger

## Purpose
Protect core accounting invariants—double-entry balance, account hierarchy, and currency handling—that underpin every Finlite capability.

## Requirements
### Requirement: Double-Entry Transactions
Every transaction MUST be composed of at least two postings whose signed amounts sum to zero.

#### Scenario: Balanced transaction persists
- **GIVEN** postings that debit Assets:Cash by 100 and credit Income:Salary by 100
- **WHEN** the transaction is created through the application layer
- **THEN** the domain accepts the transaction
- **AND** the unit of work commits the transaction without errors

#### Scenario: Unbalanced transaction is rejected
- **GIVEN** postings that debit Assets:Cash by 100 and credit Income:Salary by 90
- **WHEN** the transaction creation is attempted
- **THEN** the domain raises an `UnbalancedTransactionError`
- **AND** the transaction is not persisted

### Requirement: Account Hierarchy and Types
Accounts MUST belong to one of five types (Assets, Liabilities, Equity, Income, Expenses) and respect hierarchical codes.

#### Scenario: Creating account enforces valid type
- **GIVEN** a request to create an account with type `Liability`
- **WHEN** the application layer validates the request
- **THEN** the account is accepted only if the type is within the supported enum
- **AND** invalid types produce a validation error

#### Scenario: Account code hierarchy resolved
- **GIVEN** an account code such as `Expenses:Groceries:Fresh`
- **WHEN** listing accounts
- **THEN** the CLI displays the hierarchy using colon-separated naming
- **AND** parent accounts aggregate child balances in reports

### Requirement: Money Value Object and Currency Validation
Monetary amounts MUST use the Money value object with Decimal precision and ISO 4217 currency validation.

#### Scenario: Money rejects unsupported currency
- **GIVEN** an attempt to instantiate Money with currency `BTC`
- **WHEN** the value object validates the input
- **THEN** it raises a validation error (unsupported currency)
- **AND** the invalid money value is not accepted into domain entities
