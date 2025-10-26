## Why
- Users require a profit and loss (income statement) view to understand revenue vs expenses over a period.
- This complements the existing balance sheet without waiting for OFX ingestion work.

## What Changes
- Introduce `IncomeStatementUseCase` aggregating revenue/expense accounts with period and compare capabilities (YoY and previous period).
- Add CLI command `fin report income-statement` with the necessary flags (`--from`, `--to`, `--compare`, `--export`, `--chart`).
- Update documentation and tests covering common scenarios.

## Impact
- Touches reporting use cases, CLI presenter, documentation, and adds new tests/fixtures.
