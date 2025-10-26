## Why
- Finance power users need professional-grade balance sheet and income statement reports with period comparisons, CSV/Markdown/PDF exports, and visualization support.
- Importing OFX statements broadens bank coverage beyond Nubank CSV, aligning with roadmap goals for multi-bank ingestion.
- Consolidating these deliverables into an OpenSpec change keeps reporting scope cohesive and ensures the ingestion stack evolves consistently.

## What Changes
- Implement balance sheet and income statement use cases with CLI commands, period comparisons, and optional charts.
- Provide exporters for CSV/Markdown/PDF and integrate with Rich/Matplotlib visualization helpers.
- Add OFX parser and `fin import ofx` pipeline supporting multiple banks and mapping to statement entries.
- Update documentation with workflows and validation examples for reports and OFX imports.

## Impact
- Touches application layer (new report use cases), CLI commands, documentation, and testing harness.
- Requires ingestion infrastructure updates (parsing OFX, bank-specific adapters) and schema adjustments if statements are stored.
- Provides prerequisites for future dashboard/TUI visualizations and ensures parity across import formats.
