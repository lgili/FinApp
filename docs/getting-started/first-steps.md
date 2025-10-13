# First Steps

Now that you have Finlite installed, let's build your first chart of accounts and record some realistic transactions.

---

## 📋 Planning Your Chart of Accounts

Before creating accounts, plan your structure based on your financial tracking needs.

### Typical Personal Finance Structure

```
Assets
├── Cash
├── Checking Account
├── Savings Account
└── Investment Account

Liabilities
├── Credit Card
├── Student Loan
└── Mortgage

Equity
└── Opening Balance

Income
├── Salary
├── Freelance
├── Dividends
└── Interest

Expenses
├── Housing
│   ├── Rent/Mortgage
│   └── Utilities
├── Food
│   ├── Groceries
│   └── Restaurants
├── Transportation
│   ├── Gas
│   └── Public Transit
├── Entertainment
└── Insurance
```

---

## 🏗️ Building Your Chart of Accounts

### Step 1: Create Asset Accounts

Assets are things you own:

```bash
# Main bank account
fin accounts create -c "CHECKING" -n "Checking Account" -t ASSET

# Savings
fin accounts create -c "SAVINGS" -n "Savings Account" -t ASSET

# Cash on hand
fin accounts create -c "CASH" -n "Cash" -t ASSET
```

### Step 2: Create Liability Accounts

Liabilities are things you owe:

```bash
# Credit card
fin accounts create -c "CREDITCARD" -n "Credit Card" -t LIABILITY

# Loan (if applicable)
fin accounts create -c "CAR_LOAN" -n "Car Loan" -t LIABILITY
```

### Step 3: Create Equity Account

Equity represents your net worth:

```bash
# Opening balance account
fin accounts create -c "EQUITY" -n "Opening Balance" -t EQUITY
```

### Step 4: Create Income Accounts

Income is money coming in:

```bash
# Primary income
fin accounts create -c "SALARY" -n "Salary" -t INCOME

# Other income sources
fin accounts create -c "FREELANCE" -n "Freelance Income" -t INCOME
fin accounts create -c "INTEREST" -n "Interest Income" -t INCOME
```

### Step 5: Create Expense Accounts

Expenses are money going out:

```bash
# Housing
fin accounts create -c "RENT" -n "Rent" -t EXPENSE
fin accounts create -c "UTILITIES" -n "Utilities" -t EXPENSE

# Food
fin accounts create -c "GROCERIES" -n "Groceries" -t EXPENSE
fin accounts create -c "DINING" -n "Dining Out" -t EXPENSE

# Transportation
fin accounts create -c "GAS" -n "Gas" -t EXPENSE
fin accounts create -c "TRANSIT" -n "Public Transit" -t EXPENSE

# Other
fin accounts create -c "ENTERTAINMENT" -n "Entertainment" -t EXPENSE
fin accounts create -c "INSURANCE" -n "Insurance" -t EXPENSE
fin accounts create -c "SHOPPING" -n "Shopping" -t EXPENSE
```

### Verify Your Setup

```bash
fin accounts list
```

You should see all your accounts organized by type.

---

## 💰 Recording Your Opening Balance

Set your starting financial position:

### Checking Account Balance

```bash
fin transactions create -d "Opening balance - Checking"
```

```
Posting 1 - Account code: CHECKING
Posting 1 - Amount: 5000
Posting 2 - Account code: EQUITY
Posting 2 - Amount: -5000
Posting 3 - Account code: [Press Enter]
```

### Savings Account Balance

```bash
fin transactions create -d "Opening balance - Savings"
```

```
Posting 1 - Account code: SAVINGS
Posting 1 - Amount: 10000
Posting 2 - Account code: EQUITY
Posting 2 - Amount: -10000
```

### Cash on Hand

```bash
fin transactions create -d "Opening balance - Cash"
```

```
Posting 1 - Account code: CASH
Posting 1 - Amount: 200
Posting 2 - Account code: EQUITY
Posting 2 - Amount: -200
```

### Credit Card Balance (Liability)

If you have existing credit card debt:

```bash
fin transactions create -d "Opening balance - Credit Card"
```

```
Posting 1 - Account code: EQUITY
Posting 1 - Amount: 2000
Posting 2 - Account code: CREDITCARD
Posting 2 - Amount: -2000
```

!!! tip "Why negative for credit card?"
    Credit cards are liabilities. A negative amount means the liability increased (you owe more).

### Check Your Net Worth

```bash
# Check individual balances
fin accounts balance CHECKING   # 5000.00
fin accounts balance SAVINGS    # 10000.00
fin accounts balance CASH       # 200.00
fin accounts balance CREDITCARD # -2000.00

# Calculate: Assets - Liabilities = 13200
# This equals your Equity balance
```

---

## 📝 Recording Daily Transactions

### Example 1: Receive Monthly Salary

```bash
fin transactions create -d "Salary - October 2025" -p "My Employer"
```

```
Posting 1 - Account code: CHECKING
Posting 1 - Amount: 4500
Posting 2 - Account code: SALARY
Posting 2 - Amount: -4500
```

**New Balance**: CHECKING = $9,500

---

### Example 2: Pay Monthly Rent

```bash
fin transactions create -d "Rent - October 2025" -p "Landlord"
```

```
Posting 1 - Account code: RENT
Posting 1 - Amount: 1500
Posting 2 - Account code: CHECKING
Posting 2 - Amount: -1500
```

**New Balance**: CHECKING = $8,000

---

### Example 3: Grocery Shopping (Cash)

```bash
fin transactions create -d "Weekly groceries" -p "Whole Foods"
```

```
Posting 1 - Account code: GROCERIES
Posting 1 - Amount: 120
Posting 2 - Account code: CASH
Posting 2 - Amount: -120
```

**New Balance**: CASH = $80

---

### Example 4: Buy Something with Credit Card

```bash
fin transactions create -d "New headphones" -p "Electronics Store"
```

```
Posting 1 - Account code: SHOPPING
Posting 1 - Amount: 150
Posting 2 - Account code: CREDITCARD
Posting 2 - Amount: -150
```

**New Balance**: CREDITCARD = -$2,150 (debt increased)

---

### Example 5: Pay Credit Card Bill

```bash
fin transactions create -d "Credit card payment"
```

```
Posting 1 - Account code: CREDITCARD
Posting 1 - Amount: 500
Posting 2 - Account code: CHECKING
Posting 2 - Amount: -500
```

**Result**:
- CREDITCARD: -$2,150 + $500 = -$1,650
- CHECKING: $8,000 - $500 = $7,500

---

### Example 6: Transfer to Savings

```bash
fin transactions create -d "Monthly savings"
```

```
Posting 1 - Account code: SAVINGS
Posting 1 - Amount: 1000
Posting 2 - Account code: CHECKING
Posting 2 - Amount: -1000
```

**Result**:
- SAVINGS: $10,000 + $1,000 = $11,000
- CHECKING: $7,500 - $1,000 = $6,500

---

## 📊 Reviewing Your Finances

### View Recent Transactions

```bash
# Last 10 transactions
fin transactions list --limit 10

# This month's transactions
fin transactions list --start 2025-10-01 --end 2025-10-31

# All transactions for an account
fin transactions list --account CHECKING
```

### Check Account Balances

```bash
# Individual accounts
fin accounts balance CHECKING
fin accounts balance SAVINGS
fin accounts balance CREDITCARD

# List all accounts (shows codes)
fin accounts list
```

### Calculate Your Net Worth

```
Assets:
  CHECKING:  $6,500
  SAVINGS:   $11,000
  CASH:      $80
  ───────────────────
  Total:     $17,580

Liabilities:
  CREDITCARD: $1,650
  ───────────────────
  Total:      $1,650

Net Worth: $17,580 - $1,650 = $15,930
```

---

## 🎯 Best Practices

### 1. Record Transactions Promptly

Don't wait! Record transactions as they happen or at least daily.

```bash
# Quick command for common transactions
alias fin-grocery='fin transactions create -d "Groceries"'
alias fin-gas='fin transactions create -d "Gas"'
```

### 2. Be Consistent with Descriptions

Use clear, searchable descriptions:

✅ Good: "Weekly groceries - Whole Foods"
✅ Good: "Gas - Shell Station Main St"
❌ Bad: "stuff"
❌ Bad: "things"

### 3. Use Payee Information

Always include the payee when relevant:

```bash
fin transactions create -d "Dinner" -p "Restaurant Name"
```

### 4. Review Regularly

Make it a habit:
- **Daily**: Record transactions
- **Weekly**: Review balances
- **Monthly**: Reconcile with bank statements

### 5. Backup Your Data

```bash
# Backup command (macOS/Linux)
cp ~/.finlite/finlite.db ~/Backups/finlite-$(date +%Y%m%d).db
```

---

## 🚀 Advanced Patterns

### Split Transactions

Record a transaction that affects multiple expense categories:

```bash
fin transactions create -d "Costco shopping"
```

```
Posting 1 - Account code: GROCERIES
Posting 1 - Amount: 150
Posting 2 - Account code: SHOPPING
Posting 2 - Amount: 50
Posting 3 - Account code: CASH
Posting 3 - Amount: -200
```

### Refunds

Record a refund (reverses the original transaction):

```bash
fin transactions create -d "Refund - Returned item"
```

```
Posting 1 - Account code: CHECKING
Posting 1 - Amount: 50
Posting 2 - Account code: SHOPPING
Posting 2 - Amount: -50
```

### Interest Earned

```bash
fin transactions create -d "Savings interest"
```

```
Posting 1 - Account code: SAVINGS
Posting 1 - Amount: 25
Posting 2 - Account code: INTEREST
Posting 2 - Amount: -25
```

---

## 🐛 Common Mistakes

### Mistake 1: Wrong Account Type

❌ Creating "Salary" as an EXPENSE
✅ Create "Salary" as an INCOME

### Mistake 2: Forgetting the Signs

❌ Both postings positive
✅ One positive (debit), one negative (credit)

### Mistake 3: Not Balancing

❌ GROCERIES: +100, CASH: -50 (doesn't balance!)
✅ GROCERIES: +100, CASH: -100

---

## 📚 Next Steps

Now that you understand the basics:

1. **Learn more about double-entry**: [Double-Entry Guide](../user-guide/double-entry.md)
2. **Master the CLI**: [CLI Reference](../user-guide/cli-reference.md)
3. **Explore advanced features**: [Architecture](../architecture/overview.md)
4. **Contribute**: [Contributing Guide](../development/contributing.md)

---

## 💡 Tips

### Create a Monthly Routine

1. **Beginning of Month**:
   - Record opening balances
   - Set budget goals (mental note)

2. **Throughout Month**:
   - Record transactions daily
   - Check balances weekly

3. **End of Month**:
   - Reconcile with bank statements
   - Review spending patterns
   - Plan for next month

### Use Shell Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Quick balance checks
alias fincheck='fin accounts balance CHECKING'
alias finsave='fin accounts balance SAVINGS'

# Common transactions
alias finsalary='fin transactions create -d "Monthly salary"'
alias finrent='fin transactions create -d "Monthly rent"'

# Quick lists
alias finlast='fin transactions list --limit 10'
alias fintoday='fin transactions list --start $(date +%Y-%m-%d)'
```

---

## ❓ Need Help?

- 📖 [Full Documentation](https://lgili.github.io/finapp/)
- 🐛 [Report Issues](https://github.com/lgili/finapp/issues)
- 💬 [Ask Questions](https://github.com/lgili/finapp/discussions)

---

Happy tracking! 🎉
