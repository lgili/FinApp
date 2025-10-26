## Why
- Users want to trigger workflows (imports, reports, posting) using natural language instead of memorizing command syntax.
- The roadmap includes a `fin ask` command orchestrated via Pydantic AI with preview and confirmation; formalising this ensures safe automation.
- Natural language intents reduce friction and pave the way for future voice/UI integrations.

## What Changes
- Introduce intent schemas for core operations (import file, generate report, post entries, create rule, list transactions).
- Implement a natural language parser pipeline backed by Pydantic AI with optional LLM providers and regex fallbacks.
- Add `fin ask "<instruction>"` CLI command supporting preview, confirmation, and `--explain` flags.
- Ensure safety controls (destructive action confirmation, provider configuration) and telemetry (structured logs of intent resolution).

## Impact
- Adds a new interpreter component alongside existing CLI, interacts with multiple use cases.
- Requires configuration for local vs cloud LLM providers and caching.
- Demands comprehensive tests covering intent parsing, preview output, and failure modes.
