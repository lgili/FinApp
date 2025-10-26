## ADDED Requirements
### Requirement: Read-Only Web API
The system MUST provide a FastAPI backend exposing read-only endpoints for dashboard, inbox, ledger, reports, and investments.

#### Scenario: Fetch dashboard summary
- **WHEN** a client calls `GET /api/dashboard`
- **THEN** the server returns totals for assets, liabilities, income, expenses, and recent activity
- **AND** the response requires a valid local token

### Requirement: Web Frontend Parity
The web frontend MUST display dashboards, inbox, ledger, reports, and investment views with feature parity to CLI/TUI read-only experiences.

#### Scenario: View inbox in browser
- **WHEN** the user authenticates in the web UI
- **THEN** the inbox page lists statement entries with filters and status badges
- **AND** users can trigger read-only previews and copy command suggestions for actions

### Requirement: Local-First Operation
The web UI MUST operate with local assets and not require remote cloud services by default.

#### Scenario: Offline access
- **WHEN** the user runs the web UI locally without internet access
- **THEN** all API requests resolve against the local backend
- **AND** no external calls are required beyond optional analytics providers
