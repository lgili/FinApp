## Why
- Users need to track trades, holdings, and dividends to manage investment portfolios within the same local-first toolkit.
- The roadmap targets Brazilian PM (média ponderada) calculations, PnL reporting, and dividend tracking; capturing these requirements prevents scope drift.
- Investment insights underpin later tax reporting and web/TUI visualizations.

## What Changes
- Add domain entities for `Security`, `Trade`, `Lot`, `Dividend`, and `Price`.
- Implement use cases to import trades/dividends, calculate average cost (PM), produce holdings and PnL reports, and sync market prices.
- Provide CLI commands under `fin inv` namespace (`import-trades`, `holdings`, `pnl`, `dividends import`, `prices sync`).
- Include documentation and fixtures for brokerage CSV formats.

## Impact
- Introduces new domain modules, persistence tables, and application services for investment data.
- Requires robust tests for PM calculations, realized/unrealized gains, and dividend accounting.
- Sets the stage for tax computations and portfolio dashboards.
