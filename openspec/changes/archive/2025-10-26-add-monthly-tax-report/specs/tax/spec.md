## ADDED Requirements
### Requirement: Monthly Tax Report
The system MUST compute monthly capital gains tax summaries compliant with Brazilian regulations.

#### Scenario: Generate monthly tax report
- **WHEN** the user runs `fin tax monthly --month 2025-10`
- **THEN** the CLI outputs total sales, exempt sales, taxable gains, losses carried, and DARF base
- **AND** the user can export the report via `--export csv`

### Requirement: Loss Carryover
The tax engine MUST carry forward previous monthly losses and apply them before calculating tax due.

#### Scenario: Apply loss carryover
- **GIVEN** a R$ 2.000 loss in September and R$ 5.000 gain in October
- **WHEN** generating the October report
- **THEN** the taxable base is reduced by the R$ 2.000 carried loss
- **AND** the report documents the applied carryover
