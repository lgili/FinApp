## Why
- The original scope bundled three large capabilities (enhanced balance sheet exports, income statement reporting, and OFX ingestion). Implementing them together proved too broad for a single change.
- Breaking the work into focused changes keeps reviews manageable and allows shipping value incrementally.
- This meta-change tracks the decomposition and points to the new change IDs.

## What Changes
- Create separate proposals:
  - `enhance-balance-sheet-report` (comparisons, exports, charts)
  - `add-income-statement-report` (new report + comparisons)
  - `add-ofx-import-support` (OFX parser + CLI pipeline)
- Update project documentation to reference the staged roadmap.

## Impact
- The original proposal no longer carries implementation work; the new changes own the specs and tasks.
- Downstream specs live under the new change IDs to avoid duplication.
