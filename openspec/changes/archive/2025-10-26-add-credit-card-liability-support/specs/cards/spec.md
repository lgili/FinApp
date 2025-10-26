## ADDED Requirements
### Requirement: Credit Card Liability Accounts
The system MUST allow configuring credit card accounts as liabilities with billing cycle metadata.

#### Scenario: Create credit card account
- **WHEN** the user runs `fin accounts create --type liability --card issuer=Nubank --closing-day 7 --due-day 15`
- **THEN** the account is stored with credit card attributes
- **AND** the CLI confirms the billing configuration

### Requirement: Build Monthly Card Statement
The system MUST build a statement for a billing period aggregating purchases and installments.

#### Scenario: Generate current cycle statement
- **GIVEN** purchases exist between the previous closing date and current closing date
- **WHEN** the user runs `fin card build-statement --card Liabilities:CreditCard:Nubank --period 2025-10`
- **THEN** the CLI outputs the statement with line items, totals, and due amount
- **AND** the statement is persisted for later payoff

### Requirement: Pay Card Statement
The system MUST provide a command to pay the statement by transferring funds from an asset account.

#### Scenario: Pay outstanding statement
- **GIVEN** an open statement with amount due R$ 5.000,00
- **AND** a funding account `Assets:Bank:Checking`
- **WHEN** the user runs `fin card pay --card Liabilities:CreditCard:Nubank --from Assets:Bank:Checking --amount 5000`
- **THEN** a balanced transaction posts the payment
- **AND** the statement status updates to paid
