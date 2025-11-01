# Quick Start

Get started with Finlite in 5 minutes. This guide will walk you through creating accounts and recording your first transactions.

---

## Load Demo Data (Optional)

If you want to explore the Textual TUI or reports with realistic information, populate the database with a multi-month demo dataset:

```bash
poetry run python backend/scripts/seed_demo_data.py --months 6
```

The script is idempotent—rerunning it refreshes the same sample accounts, transactions, and pending statement entries. Use `--database-url` to target a specific SQLite file and `--start-month YYYY-MM` to control the history window.

---

## Your First Account

Let's create a cash account:

```bash
fin accounts create --code "CASH" --name "Cash" --type ASSET
```

!!! success "Account created!"
    ```
    ✅ Account created successfully!
       Code: CASH
       Name: Cash
       Type: ASSET
       Currency: USD
    ```

### Understanding Account Types

Finlite uses **five account types** based on double-entry accounting:

| Type | Description | Examples | Normal Balance |
|------|-------------|----------|----------------|
| **ASSET** | Things you own | Cash, Bank accounts, Investments | Debit (+) |
| **LIABILITY** | Things you owe | Credit cards, Loans | Credit (-) |
| **EQUITY** | Your net worth | Opening balance, Retained earnings | Credit (-) |
| **INCOME** | Money coming in | Salary, Dividends, Interest | Credit (-) |
| **EXPENSE** | Money going out | Groceries, Rent, Transport | Debit (+) |

---

## Create More Accounts

Let's build a basic chart of accounts:

```bash
# Assets
fin accounts create -c "CHECKING" -n "Checking Account" -t ASSET
fin accounts create -c "SAVINGS" -n "Savings Account" -t ASSET

# Income
fin accounts create -c "SALARY" -n "Salary" -t INCOME

# Expenses
fin accounts create -c "GROCERIES" -n "Groceries" -t EXPENSE
fin accounts create -c "RENT" -n "Rent" -t EXPENSE
fin accounts create -c "TRANSPORT" -n "Transport" -t EXPENSE

# Equity
fin accounts create -c "EQUITY" -n "Opening Balance" -t EQUITY
```

### List Your Accounts

```bash
fin accounts list
```

??? example "Expected output"
    ```
    ┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┓
    ┃ Code      ┃ Name              ┃ Type      ┃ Currency ┃
    ┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━┩
    │ CASH      │ Cash              │ ASSET     │ USD      │
    │ CHECKING  │ Checking Account  │ ASSET     │ USD      │
    │ SAVINGS   │ Savings Account   │ ASSET     │ USD      │
    │ SALARY    │ Salary            │ INCOME    │ USD      │
    │ GROCERIES │ Groceries         │ EXPENSE   │ USD      │
    │ RENT      │ Rent              │ EXPENSE   │ USD      │
    │ TRANSPORT │ Transport         │ EXPENSE   │ USD      │
    │ EQUITY    │ Opening Balance   │ EQUITY    │ USD      │
    └───────────┴───────────────────┴───────────┴──────────┘
    ```

---

## Your First Transaction

In double-entry accounting, **every transaction affects at least 2 accounts** and must **balance to zero**.

### Opening Balance

Let's record your starting cash:

```bash
fin transactions create --description "Opening balance"
```

The CLI will prompt for postings:

```
Posting 1 - Account code: CHECKING
Posting 1 - Amount (negative for credit): 5000
✓ Posting 1 added

Posting 2 - Account code: EQUITY
Posting 2 - Amount (negative for credit): -5000
✓ Posting 2 added

Posting 3 - Account code: [Press Enter to finish]

✅ Transaction created successfully!
   ID: 93ea8dbe-3649-45ee-a62d-6d93473cda55
   Description: Opening balance
   Date: 2025-10-12
   Postings: 2
```

!!! info "Why this balances"
    - CHECKING (Asset) **debited** +5000 (increases asset)
    - EQUITY **credited** -5000 (increases equity)
    - Total: 5000 + (-5000) = **0** ✓

### Check Your Balance

```bash
fin accounts balance CHECKING
```

??? success "Balance output"
    ```
    Account: Checking Account
    Code: CHECKING
    Type: ASSET
    Currency: USD
    
    Balance: 5000.00 USD
    ```

---

## Recording Income

Let's record receiving your salary:

```bash
fin transactions create -d "Monthly salary"
```

```
Posting 1 - Account code: CHECKING
Posting 1 - Amount: 3000
✓ Posting 1 added

Posting 2 - Account code: SALARY
Posting 2 - Amount: -3000
✓ Posting 2 added

Posting 3 - Account code: [Press Enter]
```

!!! tip "Understanding the transaction"
    - CHECKING (Asset) **+3000** = Money comes in
    - SALARY (Income) **-3000** = Income increases (credit)
    - Your checking balance is now: **8000 USD**

---

## Recording Expenses

### Grocery Shopping

```bash
fin transactions create -d "Weekly groceries"
```

```
Posting 1 - Account code: GROCERIES
Posting 1 - Amount: 150
✓ Posting 1 added

Posting 2 - Account code: CHECKING
Posting 2 - Amount: -150
✓ Posting 2 added

Posting 3 - Account code: [Press Enter]
```

### Rent Payment

```bash
fin transactions create -d "Monthly rent"
```

```
Posting 1 - Account code: RENT
Posting 1 - Amount: 1200
✓ Posting 1 added

Posting 2 - Account code: CHECKING
Posting 2 - Amount: -1200
✓ Posting 2 added

Posting 3 - Account code: [Press Enter]
```

!!! success "Current balance"
    Check your balance again:
    ```bash
    fin accounts balance CHECKING
    # Balance: 6650.00 USD  (8000 - 150 - 1200)
    ```

---

## View Transaction History

### All Transactions

```bash
fin transactions list
```

### Filter by Account

```bash
fin transactions list --account CHECKING
```

### Recent Transactions

```bash
fin transactions list --limit 5
```

### Date Range

```bash
fin transactions list --start 2025-10-01 --end 2025-10-31
```

---

## Double-Entry Cheat Sheet

### Common Transaction Patterns

#### Receive Money (Income)

```
Debit:  ASSET (Bank/Cash)    +X
Credit: INCOME (Salary, etc)  -X
```

#### Spend Money (Expense)

```
Debit:  EXPENSE (Groceries)   +X
Credit: ASSET (Bank/Cash)     -X
```

#### Transfer Between Accounts

```
Debit:  ASSET (Savings)       +X
Credit: ASSET (Checking)      -X
```

#### Pay with Credit Card

```
Debit:  EXPENSE (Shopping)         +X
Credit: LIABILITY (Credit Card)    -X
```

#### Pay Off Credit Card

```
Debit:  LIABILITY (Credit Card)    +X
Credit: ASSET (Checking)           -X
```

!!! tip "Remember: Debits and Credits must always equal!"
    Sum of all postings must equal zero.

---

## Debug Mode

Enable detailed logging to see what's happening:

```bash
fin --debug accounts create -c "TEST" -n "Test" -t ASSET
```

??? example "Debug output"
    ```
    2025-10-12T14:30:00 [info     ] cli_started           command=accounts
    2025-10-12T14:30:00 [info     ] creating_account      account_code=TEST account_type=ASSET
    2025-10-12T14:30:00 [info     ] account_created       account_id=abc123... account_code=TEST
    ```

---

## What's Next?

✅ You've learned the basics of Finlite!

Continue your journey:

- [First Steps](first-steps.md) - More detailed examples
- [Double-Entry Accounting](../user-guide/double-entry.md) - Deep dive into accounting principles
- [CLI Reference](../user-guide/cli-reference.md) - All available commands
- [Account Management](../user-guide/accounts.md) - Advanced account features
- [Transactions](../user-guide/transactions.md) - Complex transaction scenarios

---

## Need Help?

- 📖 [Full Documentation](../user-guide/cli-reference.md)
- 🐛 [Report Issues](https://github.com/lgili/finapp/issues)
- 💬 [Ask Questions](https://github.com/lgili/finapp/discussions)
