# CLI Reference

Complete reference for all Finlite CLI commands, options, and usage patterns.

---

## Global Options

These options are available for all commands:

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug logging (verbose output) |
| `--json-logs` | Output logs as JSON for log aggregation |
| `--version` | Show version and exit |
| `--help` | Show help message and exit |

### Examples

```bash
# Enable debug mode
fin --debug accounts list

# JSON logging for production
fin --json-logs transactions create -d "Payment"

# Check version
fin --version
```

---

## Accounts Commands

Manage financial accounts.

### `fin accounts create`

Create a new account.

**Syntax:**
```bash
fin accounts create --code CODE --name NAME --type TYPE [--currency CURRENCY] [--parent PARENT]
```

**Options:**

| Option | Short | Required | Description | Default |
|--------|-------|----------|-------------|---------|
| `--code` | `-c` | ✅ | Unique account code/identifier | - |
| `--name` | `-n` | ✅ | Account name | - |
| `--type` | `-t` | ✅ | Account type (ASSET, LIABILITY, EQUITY, INCOME, EXPENSE) | - |
| `--currency` | - | ❌ | Currency code (USD, BRL, EUR, etc.) | USD |
| `--parent` | - | ❌ | Parent account code for hierarchical accounts | - |

**Examples:**

```bash
# Create basic account
fin accounts create --code "CASH" --name "Cash" --type ASSET

# Create with custom currency
fin accounts create -c "SAVINGS-BRL" -n "Brazilian Savings" -t ASSET --currency BRL

# Create hierarchical account
fin accounts create -c "GROCERIES" -n "Groceries" -t EXPENSE --parent "FOOD"
```

**Output:**
```
✅ Account created successfully!
   Code: CASH
   Name: Cash
   Type: ASSET
   Currency: USD
```

---

### `fin accounts list`

List all accounts with optional filtering.

**Syntax:**
```bash
fin accounts list [--type TYPE]
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--type` | `-t` | Filter by account type |

**Examples:**

```bash
# List all accounts
fin accounts list

# List only assets
fin accounts list --type ASSET

# List only expenses
fin accounts list -t EXPENSE
```

**Output:**
```
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Code      ┃ Name              ┃ Type      ┃ Currency ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
│ CASH      │ Cash              │ ASSET     │ USD      │
│ CHECKING  │ Checking Account  │ ASSET     │ USD      │
│ GROCERIES │ Groceries         │ EXPENSE   │ USD      │
└───────────┴───────────────────┴───────────┴──────────┘
```

---

### `fin accounts balance`

Get the current balance of an account.

**Syntax:**
```bash
fin accounts balance ACCOUNT_CODE
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `ACCOUNT_CODE` | ✅ | Account code to check balance |

**Examples:**

```bash
# Check cash balance
fin accounts balance CASH

# Check checking account
fin accounts balance CHECKING
```

**Output:**
```
Account: Cash
Code: CASH
Type: ASSET
Currency: USD

Balance: 1000.00 USD
```

---

## Transactions Commands

Record and manage financial transactions.

### `fin transactions create`

Create a new transaction (interactive mode).

**Syntax:**
```bash
fin transactions create --description DESCRIPTION [--date DATE] [--payee PAYEE]
```

**Options:**

| Option | Short | Required | Description | Default |
|--------|-------|----------|-------------|---------|
| `--description` | `-d` | ✅ | Transaction description | - |
| `--date` | - | ❌ | Transaction date (YYYY-MM-DD) | Today |
| `--payee` | `-p` | ❌ | Payee/vendor name | - |

**Interactive Prompts:**

After providing the basic info, you'll be prompted for postings:

1. **Account code**: The account to debit/credit
2. **Amount**: Positive for debit, negative for credit
3. Repeat until you press Enter without entering an account

**Examples:**

```bash
# Simple transaction
fin transactions create -d "Salary payment"
# Posting 1 - Account code: CHECKING
# Posting 1 - Amount: 3000
# Posting 2 - Account code: SALARY
# Posting 2 - Amount: -3000

# With payee
fin transactions create -d "Grocery shopping" -p "Whole Foods"
# Posting 1 - Account code: GROCERIES
# Posting 1 - Amount: 150
# Posting 2 - Account code: CASH
# Posting 2 - Amount: -150

# With custom date
fin transactions create -d "Rent" --date 2025-10-01
# Posting 1 - Account code: RENT
# Posting 1 - Amount: 1200
# Posting 2 - Account code: CHECKING
# Posting 2 - Amount: -1200
```

**Output:**
```
✅ Transaction created successfully!
   ID: 93ea8dbe-3649-45ee-a62d-6d93473cda55
   Description: Salary payment
   Date: 2025-10-12
   Postings: 2
```

**Validation:**
- ✅ Minimum 2 postings required
- ✅ Transaction must balance (sum = 0)
- ✅ All accounts must exist

---

### `fin transactions list`

List transactions with filtering options.

**Syntax:**
```bash
fin transactions list [OPTIONS]
```

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--account` | `-a` | Filter by account code | All |
| `--start` | - | Start date (YYYY-MM-DD) | None |
| `--end` | - | End date (YYYY-MM-DD) | None |
| `--limit` | `-l` | Maximum number of results | 50 |

**Examples:**

```bash
# List all transactions
fin transactions list

# Filter by account
fin transactions list --account CHECKING

# Date range
fin transactions list --start 2025-01-01 --end 2025-12-31

# Recent transactions
fin transactions list --limit 10

# Combine filters
fin transactions list -a CASH --start 2025-10-01 --limit 20
```

**Output:**
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

---

## Database Commands

Manage the Finlite database.

### `fin init-db`

Initialize the database and run migrations.

**Syntax:**
```bash
fin init-db
```

**What it does:**
- Creates SQLite database at configured location
- Runs all Alembic migrations
- Sets up database schema

**Examples:**

```bash
# Initialize database
fin init-db
```

**Output:**
```
✅ Database initialized successfully!
   Location: ~/.finlite/finlite.db
   Tables created: accounts, transactions, postings
```

---

## Command Patterns

### Common Workflows

#### Setup New Chart of Accounts

```bash
# Assets
fin accounts create -c "CASH" -n "Cash" -t ASSET
fin accounts create -c "CHECKING" -n "Checking Account" -t ASSET
fin accounts create -c "SAVINGS" -n "Savings Account" -t ASSET

# Liabilities
fin accounts create -c "CREDITCARD" -n "Credit Card" -t LIABILITY

# Equity
fin accounts create -c "EQUITY" -n "Opening Balance" -t EQUITY

# Income
fin accounts create -c "SALARY" -n "Salary" -t INCOME
fin accounts create -c "INTEREST" -n "Interest Income" -t INCOME

# Expenses
fin accounts create -c "GROCERIES" -n "Groceries" -t EXPENSE
fin accounts create -c "RENT" -n "Rent" -t EXPENSE
fin accounts create -c "TRANSPORT" -n "Transport" -t EXPENSE
fin accounts create -c "UTILITIES" -n "Utilities" -t EXPENSE
```

#### Record Opening Balance

```bash
fin transactions create -d "Opening balance"
# CHECKING: +5000
# EQUITY: -5000
```

#### Monthly Workflow

```bash
# 1. Receive salary
fin transactions create -d "Salary - October"
# CHECKING: +3000
# SALARY: -3000

# 2. Pay rent
fin transactions create -d "Rent - October"
# RENT: +1200
# CHECKING: -1200

# 3. Daily expenses
fin transactions create -d "Groceries"
# GROCERIES: +150
# CHECKING: -150

# 4. Check balances
fin accounts balance CHECKING
fin accounts balance GROCERIES
```

---

## Exit Codes

Finlite uses standard exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Command line usage error |

---

## Environment Variables

Configure Finlite with environment variables in `.env`:

```bash
# Database location
FINLITE_DATA_DIR=~/.finlite

# Default currency
DEFAULT_CURRENCY=USD

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

---

## Tips & Tricks

### Batch Account Creation

Use a script to create multiple accounts:

```bash
#!/bin/bash
accounts=(
  "CASH:Cash:ASSET"
  "CHECKING:Checking:ASSET"
  "SAVINGS:Savings:ASSET"
  "SALARY:Salary:INCOME"
  "GROCERIES:Groceries:EXPENSE"
)

for account in "${accounts[@]}"; do
  IFS=: read -r code name type <<< "$account"
  fin accounts create -c "$code" -n "$name" -t "$type"
done
```

### Quick Balance Check

Create an alias:

```bash
# In ~/.bashrc or ~/.zshrc
alias finbal='fin accounts balance'

# Usage
finbal CASH
```

### Transaction Templates

Create shell functions for common transactions:

```bash
# Grocery transaction
grocery() {
  fin transactions create -d "Groceries - $1" -p "$2"
}

# Usage
grocery "Weekly shopping" "Whole Foods"
```

---

## Troubleshooting

### Account Not Found

```
Error: Account 'NOTEXIST' not found
```

**Solution**: Check account code with `fin accounts list`

### Unbalanced Transaction

```
Error: Transaction doesn't balance! Total: 50
```

**Solution**: Ensure debits equal credits (sum = 0)

### Database Locked

```
sqlite3.OperationalError: database is locked
```

**Solution**: Close other Finlite instances

---

## See Also

- [Quick Start Guide](../getting-started/quickstart.md)
- [Double-Entry Accounting](double-entry.md)
- [Account Management](accounts.md)
- [Transactions Guide](transactions.md)
