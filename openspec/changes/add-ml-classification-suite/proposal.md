## Why
- Manual classification of transactions is repetitive; machine-learned suggestions cut effort by 50-70% according to the roadmap.
- The plan includes training pipelines, suggestion commands, and outlier detection that should be reflected in OpenSpec artifacts.
- Consolidating ML requirements ensures reproducible models, transparency, and safe fallbacks to existing rules.

## What Changes
- Implement training pipeline (`fin ml train`) using TF-IDF + LogisticRegression with persisted models.
- Provide CLI suggestions (`fin ml suggest`) that prioritize rule-based matches and fall back to ML with confidence scoring.
- Add outlier detection (`fin detect outliers`) using IsolationForest to surface abnormal spending.
- Track metrics and produce `fin ml report` for accuracy/performance visibility.

## Impact
- Introduces ML infrastructure dependencies (scikit-learn), model storage, and evaluation pipelines.
- Touches application layer (training/suggestion use cases), infrastructure (model persistence), and CLI commands.
- Requires datasets/fixtures for testing and documentation for interpreting ML outputs.
