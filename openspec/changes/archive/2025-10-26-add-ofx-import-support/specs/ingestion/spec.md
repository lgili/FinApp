## ADDED Requirements
### Requirement: OFX Statement Import
The system MUST import OFX files into statement entries compatible with existing workflows.

#### Scenario: Import OFX file
- **WHEN** the user runs `fin import ofx statements.ofx`
- **THEN** the CLI reports how many transactions were imported and which account they map to
- **AND** StatementEntry records include external id, memo, amount, currency, and bank metadata

#### Scenario: Prevent duplicate OFX import
- **GIVEN** an OFX file that has already been imported (same checksum/external ids)
- **WHEN** the user attempts `fin import ofx statements.ofx` again
- **THEN** the command aborts with a DuplicateImport error message
- **AND** no new entries are created
