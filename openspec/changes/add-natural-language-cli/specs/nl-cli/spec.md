## ADDED Requirements
### Requirement: Natural Language Command Interface
The system MUST provide a `fin ask "<instruction>"` command that interprets natural language into supported intents.

#### Scenario: Import via natural language
- **WHEN** the user runs `fin ask "importe o arquivo extrato.csv do nubank"`
- **THEN** the CLI previews the resolved intent (`ImportFileIntent` with source `nubank`, file `extrato.csv`)
- **AND** upon confirmation, the standard import workflow executes

### Requirement: Safety Confirmation
Natural language commands MUST require confirmation before executing destructive actions.

#### Scenario: Confirm posting entries
- **WHEN** the user runs `fin ask "poste todas as entradas pendentes"`
- **THEN** the CLI displays a summary of the action with affected entries count
- **AND** the command executes only after the user confirms

### Requirement: Explain Mode
Users MUST be able to request reasoning output for how the instruction was interpreted.

#### Scenario: Explain resolution
- **WHEN** the user runs `fin ask "crie uma regra para netflix em entretenimento" --explain`
- **THEN** the CLI shows the parsed intent, parameters, and reasoning trace
- **AND** the user can accept or abort before execution
