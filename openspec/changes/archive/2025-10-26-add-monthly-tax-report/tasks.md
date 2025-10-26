## 1. Data Preparation
- [x] 1.1 Aggregate trade results per month including exemptions and loss carryovers
- [x] 1.2 Incorporate dividends/JCP and retain relevant tax classifications

## 2. Tax Report Use Case
- [x] 2.1 Implement `MonthlyTaxReportUseCase` applying Brazilian IR rules
- [x] 2.2 Provide DARF base calculation and rounding logic
- [x] 2.3 Support export formats (CSV, Markdown)

## 3. CLI & Docs
- [x] 3.1 Add `fin tax monthly --month YYYY-MM --export csv` command
- [x] 3.2 Document assumptions, configuration, and validation steps

## 4. Quality
- [x] 4.1 Unit tests with canonical tax scenarios (gains, losses, exemptions)
- [x] 4.2 Integration tests ensuring consistency with investment module outputs
- [x] 4.3 Cross-check calculations against manual reference spreadsheets
