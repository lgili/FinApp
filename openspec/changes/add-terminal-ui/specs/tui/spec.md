## ADDED Requirements
### Requirement: Launch Terminal UI
The system MUST provide a `fin tui` command that launches a Textual-based interface with keyboard navigation.

#### Scenario: Start TUI session
- **WHEN** the user runs `fin tui`
- **THEN** the application opens with header, sidebar, content, and footer regions
- **AND** arrow keys / shortcuts navigate between views without mouse usage

### Requirement: Inbox Management
The TUI MUST present imported entries with actionable shortcuts to accept, edit, delete, or apply rules.

#### Scenario: Process inbox entry
- **GIVEN** pending statement entries
- **WHEN** the user selects an entry and presses `A`
- **THEN** the entry is posted through the existing posting workflow
- **AND** the inbox updates the entry status to POSTED

### Requirement: Command Palette
The TUI MUST provide a command palette (Ctrl+K) with fuzzy search and previews for common actions.

#### Scenario: Execute command from palette
- **WHEN** the user opens the command palette and searches "cashflow"
- **THEN** the palette suggests "Generate cashflow report"
- **AND** executing it displays the report within the TUI content area
