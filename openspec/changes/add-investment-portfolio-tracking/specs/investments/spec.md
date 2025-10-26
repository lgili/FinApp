## ADDED Requirements
### Requirement: Import Trades and Track Lots
The system MUST import trade history and maintain lots using Brazilian average cost rules.

#### Scenario: Import trades CSV
- **WHEN** the user runs `fin inv import-trades trades.csv`
- **THEN** trades are loaded into the investment ledger
- **AND** lots are updated to reflect quantity and PM médio

### Requirement: Holdings Report
The system MUST provide a holdings report with market value and unrealized PnL.

#### Scenario: View holdings
- **WHEN** the user runs `fin inv holdings`
- **THEN** the CLI lists positions with quantity, PM, current price, market value, and unrealized gain/loss
- **AND** supports filtering by asset class

### Requirement: Dividend and Price Management
The system MUST import dividends and sync prices to support PnL/Yield calculations.

#### Scenario: Import dividends and sync prices
- **WHEN** the user runs `fin inv dividends import dividends.csv`
- **AND** subsequently runs `fin inv prices sync --source csv:prices.csv`
- **THEN** dividends are recorded and prices update market valuations
- **AND** `fin inv pnl --from 2025-01-01 --to 2025-12-31` reflects realized gains and dividend income
