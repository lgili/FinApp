## Why
- Users need to plan monthly spending targets and compare actual spending versus budgets directly in the CLI.
- Existing plan.md tracks budgeting goals manually; migrating to OpenSpec clarifies requirements for alerts, rollover, and reporting.
- Budget visibility supports upcoming quality-of-life work (alerts, dashboards) and ties into card imports.

## What Changes
- Introduce Budget entities covering category, amount, and period with optional rollover.
- Implement use cases to set, list, and report budgets with variance analysis.
- Provide CLI commands `fin budget set|list|report` plus alert messaging when thresholds are exceeded.
- Add optional rollover logic to carry unused amounts forward.

## Impact
- Touches domain (Budget entity/value objects), application services, persistence schemas, and CLI presenters.
- Requires new documentation and examples for setting budgets and interpreting variance.
- Enables future integrations with TUI dashboards and notifications.
