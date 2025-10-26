# Ingestion

## Purpose
Define how external financial data enters Finlite, from raw statement import to rules application and posting into balanced ledger transactions.
## Requirements
### Requirement: Nubank CSV Import
The CLI MUST import Nubank CSV files into statement entries that can later be posted as transactions.

#### Scenario: Import populates statement entries
- **GIVEN** a valid Nubank CSV file on disk
- **WHEN** the user runs `fin import nubank extrato.csv`
- **THEN** the CLI reports the number of entries imported
- **AND** the entries are stored as `StatementEntry` records pending posting

### Requirement: Rules Engine Application
The system MUST allow applying classification rules to imported entries before posting.

#### Scenario: Apply rules command updates entries
- **GIVEN** pending statement entries with merchant descriptions
- **AND** at least one rule matching `Netflix` → `Expenses:Entertainment`
- **WHEN** the user runs `fin rules apply`
- **THEN** matching entries receive the configured destination accounts and tags
- **AND** the CLI summarizes how many entries were updated

### Requirement: Posting Pending Entries
The system MUST transform classified statement entries into balanced transactions through the posting workflow.

#### Scenario: Post pending entries
- **GIVEN** classified statement entries with complete debit and credit info
- **WHEN** the user runs `fin post pending`
- **THEN** transactions are created in the ledger with balanced postings
- **AND** the original statement entries are marked as posted to prevent duplication

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

