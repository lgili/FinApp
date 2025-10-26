## Why
- Users currently lack a single CLI entry point that summarizes asset, liability, and equity balances, forcing manual queries or exports.
- A balance sheet aligns with the roadmap focus on richer reporting (Phase 10) and helps validate double-entry health with one command.
- Providing a native report keeps data local-first while offering high-level financial insight for monthly reviews.

## What Changes
- Introduce an application-layer use case that aggregates account balances by type as of a target date (default: today).
- Add a CLI command `fin reports balance-sheet` with optional `--at <date>` flag that renders totals and deltas using Rich tables.
- Persist no new data, but reuse existing repositories/unit of work to compute balances in read-only mode.
- Document the workflow and include examples in the CLI guide.

## Impact
- New reporting capability touches the reporting application module and CLI adapters; domain entities remain unchanged.
- Requires new unit tests for the aggregation service plus CLI integration coverage.
- No breaking changes anticipated; existing commands continue to operate as-is.
