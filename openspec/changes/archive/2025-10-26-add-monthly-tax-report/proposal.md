## Why
- Brazilian investors must calculate monthly capital gains tax (IR) including exemptions, carry-over losses, and DARF generation; manual spreadsheets are error-prone.
- Investments module lays groundwork but needs a dedicated tax report pipeline captured in OpenSpec.
- Automating monthly tax summaries increases trust and compliance readiness.

## What Changes
- Implement `MonthlyTaxReportUseCase` computing taxable gains, exemptions (≤ R$20k sales), and loss carryover.
- Provide CLI command `fin tax monthly --month YYYY-MM --export csv` generating detailed breakdowns and DARF base.
- Integrate with investment data (trades, dividends) and ensure rounding rules align with Receita Federal expectations.
- Document process, assumptions, and manual verification steps.

## Impact
- Builds on investment ledger data, requiring cross-module coordination.
- Introduces reporting templates and export flows tailored to tax submission.
- Needs thorough tests with reference cases to validate Brazilian tax scenarios.
