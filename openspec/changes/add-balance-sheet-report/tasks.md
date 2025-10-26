## 1. Discovery
- [ ] 1.1 Review existing account balance queries to confirm reusable repository methods
- [ ] 1.2 Align CLI UX with current reporting commands/patterns (flags, output style)

## 2. Implementation
- [ ] 2.1 Add application service to aggregate balances by account type and effective date
- [ ] 2.2 Expose the use case through dependency injection and CLI command `fin reports balance-sheet`
- [ ] 2.3 Format output with Rich tables, highlighting Assets, Liabilities, and Equity totals with net balance

## 3. Quality
- [ ] 3.1 Create unit tests for the aggregation logic (domain/application layers)
- [ ] 3.2 Add integration/CLI test covering the new command with sample data
- [ ] 3.3 Update CLI documentation with usage examples and tie into docs site navigation
