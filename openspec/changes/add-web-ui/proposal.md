## Why
- Some users prefer a browser experience mirroring CLI/TUI functionality, and the roadmap lists a read-only web UI as an optional phase.
- Defining a dedicated change ensures backend (FastAPI) and frontend (Vue 3) efforts remain aligned with local-first constraints.
- A consistent spec clarifies which dashboards, inbox features, and investment views must reach parity.

## What Changes
- Build a FastAPI backend exposing read-only endpoints for dashboard, inbox, ledger, reports, and investments.
- Implement a Vue 3 + Vite + Tailwind/DaisyUI frontend with charts (ECharts/Chart.js) and advanced search components.
- Add local token-based authentication and align API contracts with existing application services.
- Document deployment steps and caching strategy while reaffirming local-first operation.

## Impact
- Adds REST API surface area and a SPA frontend, requiring CORS/auth management.
- Requires extensive snapshot/component testing and integration tests across API/UI.
- May necessitate packaging adjustments for optional web dependencies.
