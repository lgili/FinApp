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
