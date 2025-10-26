## 1. Training Pipeline
- [ ] 1.1 Prepare dataset extraction from ledger history for supervised learning
- [ ] 1.2 Implement TF-IDF + LogisticRegression pipeline with persistence (joblib)
- [ ] 1.3 Add `fin ml train` command to build/update the model

## 2. Suggestions & Hybrid Flow
- [ ] 2.1 Implement `SuggestAccountUseCase` combining rule matches and ML fallback
- [ ] 2.2 Add `fin ml suggest --threshold <value>` CLI with confidence scores
- [ ] 2.3 Provide override/accept flows to apply suggestions

## 3. Metrics & Reporting
- [ ] 3.1 Collect accuracy/precision/recall metrics after training
- [ ] 3.2 Implement `fin ml report` to display performance and confusion matrix

## 4. Outlier Detection
- [ ] 4.1 Implement IsolationForest-based detector
- [ ] 4.2 Add `fin detect outliers --month <YYYY-MM>` CLI command with alert summaries

## 5. Quality
- [ ] 5.1 Unit tests for pipeline components and scoring
- [ ] 5.2 Integration tests on sample datasets for training and suggestions
- [ ] 5.3 Documentation outlining data requirements, retraining cadence, and interpreting outputs
