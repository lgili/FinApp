# CLI

## Purpose
Describe the command-line interface expectations so Finlite exposes cohesive namespaces, consistent UX conventions, and clear feedback for every workflow.

## Requirements
### Requirement: CLI Command Structure
The CLI MUST expose commands grouped under `accounts`, `transactions`, `import`, `rules`, `post`, `report`, and `export` namespaces aligned with Typer patterns.

#### Scenario: Accounts command usage
- **GIVEN** the CLI is installed via `fin`
- **WHEN** the user runs `fin accounts list`
- **THEN** the command executes without error
- **AND** outputs the list of accounts with balances formatted using Rich

#### Scenario: Global debug flag
- **GIVEN** a user runs any command with `--debug`
- **WHEN** the CLI starts
- **THEN** structured logging switches to verbose mode
- **AND** additional diagnostic output is displayed

### Requirement: Error Handling Feedback
The CLI MUST provide human-friendly error messages when commands fail validation.

#### Scenario: Invalid account creation handled
- **GIVEN** the user runs `fin accounts create --name ""`
- **WHEN** validation fails
- **THEN** the CLI prints a formatted error message explaining the missing name
- **AND** the program exits with a non-zero status code
