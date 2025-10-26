## ADDED Requirements
### Requirement: Minimum Coverage Threshold
The project MUST maintain at least 85% code coverage in CI, failing the pipeline if the threshold is not met.

#### Scenario: Coverage regression blocks merge
- **WHEN** the test suite runs in CI with measured coverage of 82%
- **THEN** the pipeline fails with a message indicating the threshold breach
- **AND** maintainers restore coverage before merging

### Requirement: Golden Reports
Key financial reports MUST have golden/snapshot tests to prevent regressions in presentation.

#### Scenario: Golden snapshot comparison
- **WHEN** the cashflow report formatting changes unintentionally
- **THEN** the golden test detects the diff and fails the suite
- **AND** maintainers update snapshots only when intentional changes occur
