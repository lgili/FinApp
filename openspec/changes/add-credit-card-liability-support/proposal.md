## Why
- Card statements currently require manual balancing; representing credit cards as liabilities unlocks automated statement generation and payoff workflows.
- Users need a guided flow to build monthly statements, reconcile purchases, and post consolidated payments without spreadsheet gymnastics.
- This phase is the top roadmap priority and enables accurate budgeting and reporting by distinguishing short-term liabilities.

## What Changes
- Add support for liability-type credit card accounts with metadata (issuer, closing day, due day).
- Introduce application services to assemble monthly card statements, reconcile transactions, and execute payoff transfers.
- Provide CLI commands under `fin card` for building statements, listing cards, and paying balances.
- Ensure tests cover statement closure, amortized installments, and payoff scenarios.

## Impact
- Touches domain entities (new account metadata), application layer (statement builder, payoff use cases), infrastructure (repository support), and CLI adapters.
- Requires migrations to persist credit card configuration and statement artifacts.
- Expands documentation with examples for importing, reconciling, and paying card statements.
