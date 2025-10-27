## Why
- Users now rely on the balance sheet snapshot, but need period deltas and exportable output to support reconciliation and sharing.
- Providing CSV/Markdown exports and optional charts closes gaps identified when planning pro reports, without bundling income statement or OFX scope.

## What Changes
- Extend the balance sheet report use case to compute comparisons against previous period / custom date.
- Add CLI flags (`--compare`, `--export`, `--chart`) to `fin report balance-sheet` (and new alias `fin report balance`).
- Output CSV/Markdown files, and render ASCII charts (Rich) when requested.

## Impact
- Touches reporting use case, CLI presenter, and adds export helpers.
- Documentation and tests update to cover comparison/exportr flows.
