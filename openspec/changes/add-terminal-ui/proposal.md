## Why
- Power users want a desktop-like terminal experience for reviewing imports, dashboards, and reports without issuing multiple CLI commands.
- The existing plan outlines Textual-based dashboards, inbox management, and a command palette; capturing these in OpenSpec formalizes scope and acceptance criteria.
- A cohesive TUI will streamline bulk workflows (accept/post entries, navigate accounts) and set the foundation for future UI investments.

## What Changes
- Integrate Textual to deliver a TUI shell (`fin tui`) with dashboard, inbox, ledger, accounts, reports, and rules views.
- Provide keyboard-driven navigation, command palette with fuzzy search, and actionable shortcuts for posting/importing.
- Reuse existing application services while presenting data via interactive widgets and summary charts.
- Package styling, state management, and event handling patterns to keep TUI modular and testable.

## Impact
- Adds a new interface layer module (Textual app) and supporting presenters.
- Requires infrastructure for long-lived sessions, shared DI container access, and background task orchestration.
- Demands extensive UX validation and snapshot/golden tests for stable layouts.
