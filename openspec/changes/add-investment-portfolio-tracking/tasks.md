## 1. Domain & Persistence
- [ ] 1.1 Define entities/value objects for securities, trades, lots, dividends, and prices
- [ ] 1.2 Create repositories and migrations for investment tables and lot tracking

## 2. Trade & Lot Management
- [ ] 2.1 Implement `ImportTradesUseCase` parsing brokerage CSVs
- [ ] 2.2 Build lot engine to compute Brazilian average cost (PM médio) and realized PnL
- [ ] 2.3 Implement `PnLReportUseCase` with period filters

## 3. Holdings & Dividends
- [ ] 3.1 Implement `HoldingsReportUseCase` summarizing positions, PM, market value
- [ ] 3.2 Implement `ImportDividendsUseCase` and ledger postings for dividends/JCP
- [ ] 3.3 Implement `SyncPricesUseCase` for price ingestion (CSV/external)

## 4. CLI & Docs
- [ ] 4.1 Add `fin inv import-trades`, `fin inv holdings`, `fin inv pnl`, `fin inv dividends import`, `fin inv prices sync`
- [ ] 4.2 Provide sample CSV fixtures and documentation for supported brokers

## 5. Quality
- [ ] 5.1 Unit tests for PM calculations, lot splitting, dividends
- [ ] 5.2 Integration tests covering end-to-end trade import to holdings report
- [ ] 5.3 Performance checks for large trade histories
