## Why
- Many banks export OFX; supporting this format eliminates manual CSV wrangling and broadens ingestion compatibility.
- Implementing OFX separately avoids blocking report enhancements.

## What Changes
- Build a streaming OFX parser (base + adapters) capable of handling popular Brazilian bank variants.
- Implement `ImportOFXUseCase` converting OFX transactions into statement entries, including metadata for reconciliation.
- Add CLI command `fin import ofx` and update docs/tests.

## Impact
- Extends ingestion infrastructure, introduces parser dependency, adds fixtures/tests, and updates docs.
