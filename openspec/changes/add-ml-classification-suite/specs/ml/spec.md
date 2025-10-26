## ADDED Requirements
### Requirement: Train Classification Model
The system MUST provide a command to train a classification model for transaction accounts using historical data.

#### Scenario: Train model from ledger
- **WHEN** the user runs `fin ml train`
- **THEN** the CLI reports training completion with accuracy metrics
- **AND** a serialized model is stored for future suggestions

### Requirement: Suggest Accounts with Confidence
The system MUST suggest account classifications using ML when rule-based classification does not resolve an entry.

#### Scenario: Suggest classification
- **GIVEN** imported entries lacking rule matches
- **WHEN** the user runs `fin ml suggest --threshold 0.8`
- **THEN** the CLI lists entries with suggested accounts and confidence scores
- **AND** suggestions below the threshold are flagged for manual review

### Requirement: Detect Spending Outliers
The system MUST detect abnormal spending patterns using IsolationForest and present alerts.

#### Scenario: Outlier detection report
- **WHEN** the user runs `fin detect outliers --month 2025-10`
- **THEN** the CLI outputs transactions flagged as anomalies with deviation scores
- **AND** provides guidance on reviewing or confirming the entries
