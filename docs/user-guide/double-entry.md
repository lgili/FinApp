# Double-Entry Accounting

A comprehensive guide to understanding double-entry bookkeeping in Finlite.

---

## What is Double-Entry Accounting?

Double-entry accounting is a system where **every transaction affects at least two accounts** and **always balances to zero**. This creates a self-checking system that prevents errors and provides a complete financial picture.

### The Golden Rule

!!! info "The Fundamental Equation"
    **Assets = Liabilities + Equity**
    
    And: **Income - Expenses = Change in Equity**

---

## The Five Account Types

### 1. 💰 Assets (ASSET)

**What**: Things you own that have value

**Normal Balance**: Debit (positive)

**Examples**:
- Cash
- Bank accounts (checking, savings)
- Investments
- Property
- Equipment

**Increases**: Debit (+)  
**Decreases**: Credit (-)

---

### 2. 📄 Liabilities (LIABILITY)

**What**: Money you owe to others

**Normal Balance**: Credit (negative)

**Examples**:
- Credit cards
- Loans
- Mortgages
- Accounts payable

**Increases**: Credit (-)  
**Decreases**: Debit (+)

---

### 3. 🏦 Equity (EQUITY)

**What**: Your net worth (Assets - Liabilities)

**Normal Balance**: Credit (negative)

**Examples**:
- Opening balance
- Retained earnings
- Owner's equity
- Capital contributions

**Increases**: Credit (-)  
**Decreases**: Debit (+)

---

### 4. 💵 Income (INCOME)

**What**: Money coming in

**Normal Balance**: Credit (negative)

**Examples**:
- Salary
- Dividends
- Interest income
- Sales revenue
- Rental income

**Increases**: Credit (-)  
**Decreases**: Debit (+)

---

### 5. 💸 Expenses (EXPENSE)

**What**: Money going out

**Normal Balance**: Debit (positive)

**Examples**:
- Rent
- Groceries
- Utilities
- Transport
- Insurance
- Entertainment

**Increases**: Debit (+)  
**Decreases**: Credit (-)

---

## Debit vs Credit: The Easy Way

Forget the confusing bank terminology! In accounting:

=== "Debit (+)"
    **Increases**:
    
    - ✅ Assets (Cash goes up)
    - ✅ Expenses (You spent money)
    
    **Decreases**:
    
    - ❌ Liabilities (Paid off debt)
    - ❌ Equity (Withdrew money)
    - ❌ Income (Refund/correction)

=== "Credit (-)"
    **Increases**:
    
    - ✅ Liabilities (Borrowed money)
    - ✅ Equity (Added capital)
    - ✅ Income (Earned money)
    
    **Decreases**:
    
    - ❌ Assets (Cash goes down)
    - ❌ Expenses (Refund/correction)

---

## The T-Account Visual

Each account can be visualized as a "T":

```
        ASSET (Cash)
    ──────────┬──────────
    Debit (+) │ Credit (-)
    ──────────┼──────────
    +1000     │ -150
    +3000     │ -1200
    ──────────┼──────────
    Balance: 2650 (Debit)
```

```
        INCOME (Salary)
    ──────────┬──────────
    Debit (+) │ Credit (-)
    ──────────┼──────────
              │ -3000
              │ -3000
    ──────────┼──────────
    Balance: -6000 (Credit)
```

---

## Transaction Examples

### Example 1: Opening Balance

You start with $5,000 in your checking account.

```python
Transaction: "Opening balance"
─────────────────────────────────
CHECKING (Asset)     +5000  ← Money in
EQUITY              -5000  ← Your net worth
─────────────────────────────────
Total:                   0  ✓ Balanced
```

**Why it works**:
- Assets increased by $5,000
- Equity increased by $5,000
- Assets = Equity ✓

---

### Example 2: Receive Salary

You receive your $3,000 salary.

```python
Transaction: "Monthly salary"
─────────────────────────────────
CHECKING (Asset)     +3000  ← Bank account increases
SALARY (Income)      -3000  ← Income earned
─────────────────────────────────
Total:                   0  ✓ Balanced
```

**Why it works**:
- Assets increased (you have more cash)
- Income increased (credit means income up)
- Your equity increased by $3,000

---

### Example 3: Pay Rent

You pay $1,200 for rent.

```python
Transaction: "Monthly rent"
─────────────────────────────────
RENT (Expense)       +1200  ← You spent money
CHECKING (Asset)     -1200  ← Bank account decreases
─────────────────────────────────
Total:                   0  ✓ Balanced
```

**Why it works**:
- Expenses increased (you spent money)
- Assets decreased (less cash)
- Your equity decreased by $1,200

---

### Example 4: Grocery Shopping

You buy $150 worth of groceries with cash.

```python
Transaction: "Weekly groceries"
─────────────────────────────────
GROCERIES (Expense)   +150  ← You spent money
CASH (Asset)          -150  ← Cash decreases
─────────────────────────────────
Total:                   0  ✓ Balanced
```

---

### Example 5: Transfer Between Accounts

You move $500 from checking to savings.

```python
Transaction: "Transfer to savings"
─────────────────────────────────
SAVINGS (Asset)       +500  ← Savings increases
CHECKING (Asset)      -500  ← Checking decreases
─────────────────────────────────
Total:                   0  ✓ Balanced
```

**Why it works**:
- Both are assets
- Total assets unchanged (just moved)

---

### Example 6: Buy with Credit Card

You buy $200 of clothes with your credit card.

```python
Transaction: "Clothes shopping"
─────────────────────────────────
SHOPPING (Expense)    +200  ← You spent money
CREDITCARD (Liability) -200  ← Debt increased
─────────────────────────────────
Total:                   0  ✓ Balanced
```

**Why it works**:
- Expenses increased (you bought something)
- Liabilities increased (credit means liability up)
- Your equity decreased by $200

---

### Example 7: Pay Off Credit Card

You pay $200 from your checking account to your credit card.

```python
Transaction: "Credit card payment"
─────────────────────────────────
CREDITCARD (Liability) +200  ← Debt decreases
CHECKING (Asset)       -200  ← Cash decreases
─────────────────────────────────
Total:                   0  ✓ Balanced
```

**Why it works**:
- Liabilities decreased (debit means liability down)
- Assets decreased (less cash)
- Your equity unchanged (just reshuffled)

---

## Common Transaction Patterns

### Income Transactions

| Transaction | Debit | Credit |
|-------------|-------|--------|
| Salary received | CHECKING (+) | SALARY (-) |
| Dividend received | CHECKING (+) | DIVIDENDS (-) |
| Interest earned | SAVINGS (+) | INTEREST (-) |
| Freelance payment | CHECKING (+) | FREELANCE (-) |

### Expense Transactions

| Transaction | Debit | Credit |
|-------------|-------|--------|
| Rent payment | RENT (+) | CHECKING (-) |
| Grocery shopping | GROCERIES (+) | CASH (-) |
| Utility bill | UTILITIES (+) | CHECKING (-) |
| Gas for car | TRANSPORT (+) | CASH (-) |

### Asset Transfers

| Transaction | Debit | Credit |
|-------------|-------|--------|
| Checking → Savings | SAVINGS (+) | CHECKING (-) |
| Cash → Checking | CHECKING (+) | CASH (-) |
| Withdraw cash | CASH (+) | CHECKING (-) |

### Credit Card Transactions

| Transaction | Debit | Credit |
|-------------|-------|--------|
| Buy with CC | EXPENSE (+) | CREDITCARD (-) |
| Pay off CC | CREDITCARD (+) | CHECKING (-) |
| CC interest | INTEREST_EXP (+) | CREDITCARD (-) |

---

## The Accounting Equation

### Starting Position

```
Assets = Liabilities + Equity
$5,000 = $0 + $5,000
```

### After Receiving Salary (+$3,000)

```
Assets = Liabilities + Equity + Income
$8,000 = $0 + $5,000 + $3,000
```

### After Paying Rent (-$1,200)

```
Assets = Liabilities + Equity + Income - Expenses
$6,800 = $0 + $5,000 + $3,000 - $1,200
```

### Simplified

```
Assets = Liabilities + Equity
$6,800 = $0 + $6,800
```

Your net worth increased by $1,800 (Income - Expenses).

---

## Why Double-Entry is Powerful

### 1. Self-Checking ✓

Every transaction must balance. If it doesn't, you know there's an error.

```python
# This will fail validation
CHECKING: +1000
SALARY: -500
# Error: Doesn't balance! Total: 500
```

### 2. Complete Picture 📊

You always know:
- Where money came from (credit side)
- Where money went to (debit side)

### 3. Financial Statements 📈

From your transactions, you can generate:
- **Balance Sheet**: Assets, Liabilities, Equity at a point in time
- **Income Statement**: Income and Expenses over a period
- **Cash Flow**: How cash moved

### 4. Audit Trail 🔍

Every transaction is recorded with:
- Description
- Date
- All affected accounts
- Amounts

---

## Common Mistakes

### Mistake 1: Wrong Signs

❌ **Wrong**:
```python
# Receiving salary
CHECKING: -3000  # Wrong sign!
SALARY: +3000    # Wrong sign!
```

✅ **Correct**:
```python
# Receiving salary
CHECKING: +3000  # Asset increases
SALARY: -3000    # Income increases (credit)
```

### Mistake 2: Single-Entry

❌ **Wrong**:
```python
# Missing the other side
GROCERIES: +150
# Where did the money come from?
```

✅ **Correct**:
```python
GROCERIES: +150
CASH: -150
```

### Mistake 3: Unbalanced

❌ **Wrong**:
```python
RENT: +1200
CHECKING: -1000
# Total: 200 (doesn't balance!)
```

✅ **Correct**:
```python
RENT: +1200
CHECKING: -1200
# Total: 0 ✓
```

---

## Finlite Examples

### Complete Monthly Cycle

```bash
# 1. Opening balance
fin transactions create -d "Opening balance"
# CHECKING: +5000, EQUITY: -5000

# 2. Receive salary
fin transactions create -d "Salary - October"
# CHECKING: +3000, SALARY: -3000

# 3. Pay rent
fin transactions create -d "Rent - October"
# RENT: +1200, CHECKING: -1200

# 4. Groceries (4 times)
fin transactions create -d "Groceries - Week 1"
# GROCERIES: +150, CHECKING: -150

fin transactions create -d "Groceries - Week 2"
# GROCERIES: +150, CHECKING: -150

fin transactions create -d "Groceries - Week 3"
# GROCERIES: +150, CHECKING: -150

fin transactions create -d "Groceries - Week 4"
# GROCERIES: +150, CHECKING: -150

# 5. Transport
fin transactions create -d "Gas"
# TRANSPORT: +100, CHECKING: -100

# 6. Utilities
fin transactions create -d "Electric bill"
# UTILITIES: +80, CHECKING: -80

# 7. Transfer to savings
fin transactions create -d "Monthly savings"
# SAVINGS: +500, CHECKING: -500

# Check final balances
fin accounts balance CHECKING   # 5670
fin accounts balance SAVINGS    # 500
fin accounts balance GROCERIES  # 600
```

### Result

```
Assets:
  CHECKING:  $5,670
  SAVINGS:   $500
  Total:     $6,170

Income:
  SALARY:    $3,000

Expenses:
  RENT:      $1,200
  GROCERIES: $600
  TRANSPORT: $100
  UTILITIES: $80
  Total:     $1,980

Net Worth: $6,170 (Starting $5,000 + Net Income $1,020)
```

---

## Quick Reference

### Sign Convention in Finlite

| Account Type | Increase | Decrease |
|--------------|----------|----------|
| ASSET | + (Debit) | - (Credit) |
| LIABILITY | - (Credit) | + (Debit) |
| EQUITY | - (Credit) | + (Debit) |
| INCOME | - (Credit) | + (Debit) |
| EXPENSE | + (Debit) | - (Credit) |

### Remember

- Debit = Positive number in Finlite
- Credit = Negative number in Finlite
- Every transaction sums to zero
- Minimum 2 postings per transaction

---

## Further Reading

- [CLI Reference](cli-reference.md) - All Finlite commands
- [Account Management](accounts.md) - Managing accounts
- [Transactions Guide](transactions.md) - Recording transactions
- [Quick Start](../getting-started/quickstart.md) - Get started quickly
