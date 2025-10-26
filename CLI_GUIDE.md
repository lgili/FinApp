# Finlite CLI Guide

Complete guide to using Finlite's command-line interface.

## Installation

```bash
cd backend
pip install -e .
```

## Global Options

All commands support these global options:

```bash
fin --debug            # Enable debug logging
fin --json-logs        # Output logs as JSON (for log aggregation)
fin --version          # Show version
fin --help             # Show help
```

## Account Management

### Create Account

Create a new account:

```bash
fin accounts create --code "CASH001" --name "Cash" --type ASSET
fin accounts create -c "BANK001" -n "Checking Account" -t ASSET
fin accounts create -c "INCOME001" -n "Salary" -t INCOME --currency BRL
```

**Options:**
- `--code, -c` (required): Account code/identifier
- `--name, -n` (required): Account name
- `--type, -t` (required): Account type (ASSET, LIABILITY, EQUITY, INCOME, EXPENSE)
- `--currency` (optional): Currency code (default: USD)
- `--parent` (optional): Parent account code for hierarchical accounts

### List Accounts

List all accounts:

```bash
# List all accounts
fin accounts list

# Filter by type
fin accounts list --type ASSET
fin accounts list --type EXPENSE
```

**Example Output:**
```
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ Code    ┃ Name              ┃ Type    ┃ Currency ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ CASH001 │ Cash              │ ASSET   │ USD      │
│ BANK001 │ Checking Account  │ ASSET   │ USD      │
│ INC001  │ Salary            │ INCOME  │ USD      │
└─────────┴───────────────────┴─────────┴──────────┘
```

### Get Account Balance

Get the current balance of an account:

```bash
fin accounts balance CASH001
fin accounts balance BANK001
```

**Example Output:**
```
Account: Cash
Code: CASH001
Type: ASSET
Currency: USD

Balance: 1000.00 USD
```

## Transaction Management

### Create Transaction

Create a new transaction (interactive mode):

```bash
fin transactions create --description "Salary payment"
```

The command will prompt for postings:
```
Posting 1 - Account code: BANK001
Posting 1 - Amount (negative for credit): 3000
✓ Posting 1 added

Posting 2 - Account code: INCOME001
Posting 2 - Amount (negative for credit): -3000
✓ Posting 2 added

Posting 3 - Account code: [Press Enter to finish]

✅ Transaction created successfully!
   ID: 93ea8dbe-3649-45ee-a62d-6d93473cda55
   Description: Salary payment
   Date: 2025-10-12
   Postings: 2
```

**Options:**
- `--description, -d` (required): Transaction description
- `--date` (optional): Transaction date (YYYY-MM-DD, default: today)
- `--payee, -p` (optional): Payee/vendor name

**Rules:**
- Minimum 2 postings required
- Transaction must balance (sum = 0)
- Use positive amounts for debits, negative for credits

### List Transactions

List transactions with optional filters:

```bash
# List all transactions
fin transactions list

# Filter by account
fin transactions list --account CASH001

# Filter by date range
fin transactions list --start 2025-01-01 --end 2025-12-31

# Limit results
fin transactions list --limit 10

# Combine filters
fin transactions list -a BANK001 --start 2025-10-01 --limit 20
```

**Example Output:**
```
Transactions (3 results)
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Date       ┃ Description        ┃ Payee    ┃ Postings ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 2025-10-12 │ Salary payment     │ Company  │        2 │
│ 2025-10-11 │ Grocery shopping   │ Market   │        2 │
│ 2025-10-10 │ Rent payment       │ Landlord │        2 │
└────────────┴────────────────────┴──────────┴──────────┘

Show posting details? [y/N]:
```

## Import Bank Statements

### Import OFX Files

Import bank statements in OFX format (Open Financial Exchange):

```bash
# Import OFX statement
fin import ofx ~/Downloads/bank-statement.ofx

# Import with specific currency
fin import ofx statement.ofx --currency BRL

# Import with account hint for easier reconciliation
fin import ofx statement.ofx --account "Assets:BankAccount" --currency USD
```

**Options:**
- `file_path` (required): Path to OFX file
- `--currency, -c` (optional): Default currency (BRL, USD, etc.) - default: BRL
- `--account, -a` (optional): Suggested account for entries (helps with matching)

**Supported OFX Features:**
- FITID (transaction ID) for deduplication
- DTPOSTED (transaction date)
- TRNAMT (amount)
- NAME (payee/merchant)
- MEMO (description)
- CURRENCY (transaction-level or header-level)
- Multi-currency transactions

**Deduplication:**
Files with the same SHA256 hash will be automatically rejected to prevent duplicate imports.

**Example Output:**
```
Importing OFX statement: statement.ofx

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃        Import Complete               ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ✓ Import successful!                 │
│                                       │
│ Batch ID: 3fe45d67-9e70-4b1b-a008... │
│ Entries: 15                           │
│ SHA256: a1b2c3d4e5f6...               │
└───────────────────────────────────────┘

Next steps:
  • Review entries: fin import entries 3fe45d67-...
  • Match to transactions: fin match auto (coming soon)
```

### Import Nubank CSV

Import Nubank credit card statements in CSV format:

```bash
# Import Nubank CSV
fin import nubank ~/Downloads/nubank-2025-10.csv

# Import with account hint
fin import nubank statement.csv --account "Liabilities:Nubank" --currency BRL
```

**Note:** Same deduplication and entry review process as OFX imports.

### List Import Batches

View all imported statement batches:

```bash
# List all imports
fin import list

# Filter by status
fin import list --status COMPLETED
fin import list --status PENDING

# Limit results
fin import list --limit 20
```

**Example Output:**
```
                  Import Batches (10 shown)
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Batch ID       ┃ Source    ┃ Status ┃ Entries┃ Filename       ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ 3fe45d67-9e... │ OFX       │ COMPLE │    15  │ statement.ofx  │
│ 7a8b9c0d-1e... │ NUBANK_C… │ COMPLE │    42  │ nubank-oct.csv │
│ 2f3e4d5c-6a... │ OFX       │ COMPLE │     8  │ bank-sep.ofx   │
└────────────────┴───────────┴────────┴────────┴────────────────┘
```

### View Statement Entries

Show entries from a specific import batch:

```bash
# Show all entries in a batch
fin import entries <batch-id>

# Filter by status
fin import entries <batch-id> --status IMPORTED
fin import entries <batch-id> --status POSTED

# Limit results
fin import entries <batch-id> --limit 50
```

**Example Output:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃     Import Batch Details        ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Batch: 3fe45d67-9e70-4b1b-a008  │
│ Source: OFX                      │
│ Status: COMPLETED                │
│ Total Entries: 15                │
│ Filename: statement.ofx          │
└──────────────────────────────────┘

           Statement Entries (15 shown)
┏━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┓
┃ External ID ┃ Date     ┃ Payee      ┃ Amount  ┃ Status┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━┩
│ TXN001      │ 2025-10… │ Store ABC  │  -150.50│ IMPOR…│
│ TXN002      │ 2025-10… │ Employer   │ 5,000.00│ IMPOR…│
│ TXN003      │ 2025-10… │ Landlord   │-1,200.00│ IMPOR…│
└─────────────┴──────────┴────────────┴─────────┴───────┘
```

### OFX Format Details

**What is OFX?**
OFX (Open Financial Exchange) is a standard format for exchanging financial data. Most banks and financial institutions support exporting transactions in OFX format.

**How to get OFX files:**
1. Log into your bank's website
2. Go to transaction history or statements
3. Look for "Export" or "Download" options
4. Select "OFX" or "Microsoft Money" format
5. Save the file and import with `fin import ofx <file>`

**Supported Banks (Brazilian):**
- Most Brazilian banks support OFX export
- Nubank: Use CSV import instead (`fin import nubank`)
- Banco do Brasil, Bradesco, Itaú, Santander: OFX supported
- Inter, C6, Nubank: Check export options in app/website

**Troubleshooting OFX Imports:**

1. **"File already imported" error:**
   - The same file (based on SHA256 hash) was already imported
   - This prevents duplicate entries
   - If you need to re-import, check existing batches with `fin import list`

2. **"Invalid date format" error:**
   - OFX file may be corrupted or in non-standard format
   - Try downloading the file again from your bank
   - Check if file is actually OFX (open in text editor, should start with "OFXHEADER")

3. **Wrong amounts or currencies:**
   - Specify correct default currency with `--currency`
   - Check if OFX file contains CURDEF or CURRENCY tags
   - OFX amounts are always in decimal format (100.50, not 100,50)

4. **Missing transactions:**
   - Check the date range when exporting from bank
   - Some banks limit the number of transactions per export
   - You may need to export multiple periods and import separately

5. **Encoding issues (special characters):**
   - The import automatically tries UTF-8, then falls back to Latin-1
   - If characters still appear wrong, contact your bank for encoding info

**Next Steps After Import:**
1. Review imported entries: `fin import entries <batch-id>`
2. Apply matching rules: `fin match auto` (coming soon)
3. Post matched entries to ledger: `fin post <entry-id>` (coming soon)
4. Generate reports: `fin report income-statement`

## Reports

### Income Statement

Generate a profit and loss (income statement) report for a period:

```bash
# Basic income statement for current year
fin report income-statement

# Specific period
fin report income-statement --from 2025-01-01 --to 2025-12-31

# Monthly report
fin report income-statement --from 2025-10-01 --to 2025-10-31

# Different currency
fin report income-statement --from 2025-01-01 --to 2025-12-31 --currency USD
```

**Options:**
- `--from, -f` (optional): Start date (YYYY-MM-DD, default: January 1st of current year)
- `--to, -t` (optional): End date (YYYY-MM-DD, default: today)
- `--currency, -c` (optional): Currency code (default: BRL)
- `--compare` (optional): Comparison mode - `previous` (previous period) or `yoy` (year-over-year)
- `--export` (optional): Export to file (CSV or Markdown): e.g., `report.csv` or `report.md`
- `--chart` (optional): Show visual chart of revenue vs expenses

**Example Output:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              Income Statement Summary                    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Period: 2025-10-01 to 2025-10-31                        │
│ Currency: BRL                                             │
│                                                           │
│ Total Revenue: 5,000.00 BRL                              │
│ Total Expenses: 2,300.00 BRL                             │
│ Net Income: 2,700.00 BRL                                 │
└───────────────────────────────────────────────────────────┘

                          Revenue
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┓
┃ Account        ┃ Amount     ┃ % of Revenue┃ Txns ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━┩
│ Income:Salary  │ 5,000.00   │ 100.0%      │    1 │
│ Total Revenue  │ 5,000.00   │             │      │
└────────────────┴────────────┴─────────────┴──────┘

                         Expenses
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┓
┃ Account        ┃ Amount     ┃ % of Revenue┃ Txns ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━┩
│ Expenses:Rent  │ 1,500.00   │ 30.0%       │    1 │
│ Expenses:Food  │   800.00   │ 16.0%       │    1 │
│ Total Expenses │ 2,300.00   │             │      │
└────────────────┴────────────┴─────────────┴──────┘
```

#### Comparison Modes

Compare performance across periods:

```bash
# Compare to previous period (same length)
fin report income-statement --from 2025-10-01 --to 2025-10-31 --compare previous

# Compare year-over-year (same period last year)
fin report income-statement --from 2025-10-01 --to 2025-10-31 --compare yoy
```

**Example Output with Comparison:**
```
                         Revenue
┏━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Account       ┃ Amount ┃ % Rev ┃ Txns┃ Comparison     ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━╇━━━━━━━━━━━━━━━━┩
│ Income:Salary │ 5,000  │ 100%  │  1  │ 4,500 → ▲ 500  │
│               │        │       │     │ (+11.1%)       │
└───────────────┴────────┴───────┴─────┴────────────────┘
```

#### Export Options

Export reports to CSV or Markdown for analysis:

```bash
# Export to CSV
fin report income-statement --from 2025-01-01 --to 2025-12-31 --export annual_report.csv

# Export to Markdown
fin report income-statement --from 2025-01-01 --to 2025-12-31 --export annual_report.md
```

**CSV Output Example:**
```csv
Income Statement Report
Period: 2025-01-01 to 2025-12-31,Currency: BRL

REVENUE
Account Code,Account Name,Amount,Transactions
Income:Salary,Salary,60000.00,12
Total Revenue,,60000.00,

EXPENSES
Account Code,Account Name,Amount,Transactions
Expenses:Rent,Rent,18000.00,12
Expenses:Food,Food,9600.00,24
Total Expenses,,27600.00,

NET INCOME,,32400.00,
```

#### Visual Charts

Display simple charts for quick insights:

```bash
fin report income-statement --from 2025-10-01 --to 2025-10-31 --chart
```

**Example Output:**
```
Revenue vs Expenses Chart

Revenue (5,000.00):
██████████████████████████████████████████████████

Expenses (2,300.00):
███████████████████████

Net Income: 2,700.00
```

#### Interpretation Tips

**Understanding the Report:**

1. **Revenue Section**: Shows all income accounts (salary, sales, etc.)
   - Sorted by amount (highest first)
   - Shows percentage of total revenue
   - Helps identify main income sources

2. **Expenses Section**: Shows all expense accounts (rent, food, etc.)
   - Sorted by amount (highest first)
   - Shows percentage of revenue for expense ratio analysis
   - Helps identify largest spending categories

3. **Net Income**: Revenue - Expenses
   - Positive = Profit
   - Negative = Loss
   - Compare across periods to track trends

**Common Use Cases:**

- **Monthly Budgeting**: Compare actual vs planned spending
  ```bash
  fin report income-statement --from 2025-10-01 --to 2025-10-31
  ```

- **Year-End Review**: Analyze full year performance
  ```bash
  fin report income-statement --from 2025-01-01 --to 2025-12-31 --export year_2025.csv
  ```

- **Growth Tracking**: Monitor year-over-year growth
  ```bash
  fin report income-statement --from 2025-Q1 --compare yoy
  ```

- **Quarterly Reports**: Track business performance
  ```bash
  fin report income-statement --from 2025-10-01 --to 2025-12-31 --compare previous
  ```

## Examples

### Basic Setup

```bash
# Create chart of accounts
fin accounts create -c "ASSETS" -n "Assets" -t ASSET
fin accounts create -c "CHECKING" -n "Checking Account" -t ASSET
fin accounts create -c "CASH" -n "Cash" -t ASSET
fin accounts create -c "INCOME" -n "Income" -t INCOME
fin accounts create -c "SALARY" -n "Salary" -t INCOME
fin accounts create -c "EXPENSES" -n "Expenses" -t EXPENSE
fin accounts create -c "FOOD" -n "Food" -t EXPENSE
fin accounts create -c "RENT" -n "Rent" -t EXPENSE

# Verify accounts
fin accounts list
```

### Record Income

```bash
# Salary received (debit CHECKING, credit INCOME)
fin transactions create -d "Monthly salary"
# Posting 1: CHECKING, 5000
# Posting 2: SALARY, -5000

# Check balance
fin accounts balance CHECKING
# Balance: 5000.00 USD
```

### Record Expenses

```bash
# Grocery shopping (debit FOOD, credit CHECKING)
fin transactions create -d "Grocery shopping" -p "Supermarket"
# Posting 1: FOOD, 150
# Posting 2: CHECKING, -150

# Rent payment (debit RENT, credit CHECKING)
fin transactions create -d "Monthly rent"
# Posting 1: RENT, 1200
# Posting 2: CHECKING, -1200

# Check updated balance
fin accounts balance CHECKING
# Balance: 3650.00 USD
```

### View Transaction History

```bash
# All transactions for CHECKING account
fin transactions list --account CHECKING

# Transactions for current month
fin transactions list --start 2025-10-01 --end 2025-10-31

# Recent transactions
fin transactions list --limit 10
```

## Double-Entry Accounting Rules

Finlite uses double-entry bookkeeping:

1. **Every transaction affects at least 2 accounts**
2. **Debits must equal credits** (transaction sum = 0)
3. **Debit increases**: Assets, Expenses
4. **Credit increases**: Liabilities, Equity, Income

### Debit/Credit Reference

| Account Type | Debit (+)  | Credit (-) |
|--------------|------------|------------|
| ASSET        | Increase   | Decrease   |
| LIABILITY    | Decrease   | Increase   |
| EQUITY       | Decrease   | Increase   |
| INCOME       | Decrease   | Increase   |
| EXPENSE      | Increase   | Decrease   |

### Transaction Examples

**Receive salary** (increase ASSET, increase INCOME):
```
Debit:  CHECKING   +3000
Credit: SALARY     -3000
```

**Pay rent** (increase EXPENSE, decrease ASSET):
```
Debit:  RENT       +1200
Credit: CHECKING   -1200
```

**Buy with credit card** (increase EXPENSE, increase LIABILITY):
```
Debit:  SHOPPING   +500
Credit: CREDITCARD -500
```

## Logging

Enable logging for debugging or audit trails:

```bash
# Debug logging (human-readable)
fin --debug accounts list

# JSON logging (for log aggregation)
fin --json-logs accounts create -c "TEST" -n "Test" -t ASSET

# Combine with commands
fin --debug transactions create -d "Test transaction"
```

**Log Output Examples:**

Debug mode (colorized):
```
2025-10-12T14:30:00 [info     ] creating_account      account_code=CASH001 account_type=ASSET
2025-10-12T14:30:00 [info     ] account_created       account_id=abc123... account_code=CASH001
```

JSON mode:
```json
{"event":"account_created","level":"info","timestamp":"2025-10-12T14:30:00","account_id":"abc123..."}
```

## Troubleshooting

### Account Already Exists

```bash
fin accounts create -c "CASH" -n "Cash" -t ASSET
# Error: Account with code 'CASH' already exists
```

**Solution**: Use a different code or list existing accounts

### Unbalanced Transaction

```bash
fin transactions create -d "Test"
# Posting 1: CASH, 100
# Posting 2: INCOME, -50
# Error: Transaction doesn't balance! Total: 50
```

**Solution**: Ensure debits equal credits (sum = 0)

### Account Not Found

```bash
fin transactions create -d "Test"
# Posting 1: NOTEXIST, 100
# Error: Account 'NOTEXIST' not found
```

**Solution**: Create the account first or check spelling

## Tips

1. **Use consistent naming**: `ASSET:CHECKING`, `EXPENSE:FOOD`, etc.
2. **Check balances regularly**: `fin accounts balance <code>`
3. **Filter transactions**: Use `--account` and `--start/--end` for reports
4. **Enable debug mode**: Use `--debug` when troubleshooting
5. **Keep descriptions clear**: Use meaningful transaction descriptions

## Advanced Usage

### Scripting

Create accounts from a script:

```bash
#!/bin/bash
# setup-accounts.sh

accounts=(
  "CASH:Cash:ASSET"
  "CHECKING:Checking:ASSET"
  "SAVINGS:Savings:ASSET"
  "SALARY:Salary:INCOME"
  "FOOD:Food:EXPENSE"
  "RENT:Rent:EXPENSE"
)

for account in "${accounts[@]}"; do
  IFS=: read -r code name type <<< "$account"
  fin accounts create -c "$code" -n "$name" -t "$type"
done
```

### Export for Analysis

```bash
# Export transaction list
fin transactions list --limit 1000 > transactions.txt

# With JSON logging for parsing
fin --json-logs transactions list --limit 1000 > transactions.jsonl
```

## Next Steps

- Learn about [Architecture](../ARCHITECTURE.md)
- Read [Development Guide](../backend/README.md)
- Explore [Domain Layer](../backend/finlite/domain/README.md)
- Check [API Documentation](../backend/finlite/application/README.md)

## Support

For issues or questions:
- Check [GitHub Issues](https://github.com/lgili/finapp/issues)
- Read [MIGRATION_ROADMAP.md](../MIGRATION_ROADMAP.md)
- Review [plan.md](../plan.md)
