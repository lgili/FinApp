# Bank Statement Import

Import bank statements from CSV and OFX files into Finlite for review and matching to transactions.

## Overview

The bank statement import feature allows you to:

1. **Import** transactions from external sources (Nubank CSV, OFX files)
2. **Review** imported entries before posting
3. **Match** entries to existing accounts (manual or automatic)
4. **Post** matched entries as transactions
5. **Avoid duplicates** via SHA256 file hashing

## Supported Formats

### Nubank CSV

Nubank provides a CSV export of your transactions. The format typically includes:

```csv
date,description,amount,id
2025-10-01,Salary,5000.00,SAL-001
2025-10-02,Supermarket,-250.50,SUP-001
2025-10-03,Coffee Shop,-12.00,COF-001
```

**Required Columns:**
- `date` or `data` - Transaction date (ISO format `YYYY-MM-DD` or Brazilian format `DD/MM/YYYY`)
- `description` or `descrição` - Transaction description
- `amount` or `valor` - Transaction amount (positive for credits, negative for debits)

**Optional Columns:**
- `id` or `identificador` - External ID for the transaction
- `currency` or `moeda` - Currency code (defaults to BRL if not specified)

### OFX Files

*Coming soon!* OFX (Open Financial Exchange) support is tracked under `openspec change: add-ofx-import-support`.

## CLI Commands

### Import Nubank CSV

```bash
fin import nubank <file-path> [OPTIONS]
```

**Options:**
- `--currency, -c <CODE>` - Default currency (default: BRL)
- `--account, -a <ACCOUNT>` - Suggested account for entries

**Examples:**

```bash
# Basic import
fin import nubank ~/Downloads/nubank-2025-10.csv

# Specify currency and account hint
fin import nubank statement.csv --currency USD --account "Assets:Nubank"
```

**Output:**

```
✓ Import successful!

Batch ID: 123e4567-e89b-12d3-a456-426614174000
Entries: 42
SHA256: abc123def456...

Next steps:
  • Review entries: fin import entries 123e4567-e89b-12d3-a456-426614174000
  • Match to transactions: fin match auto (coming soon)
```

### List Import Batches

```bash
fin import list [OPTIONS]
```

**Options:**
- `--status, -s <STATUS>` - Filter by status (PENDING, COMPLETED, FAILED, REVERSED)
- `--limit, -n <NUMBER>` - Number of results to show (default: 50)

**Examples:**

```bash
# List all imports
fin import list

# List only completed imports
fin import list --status COMPLETED

# Show last 10 imports
fin import list --limit 10
```

**Output:**

```
                      Import Batches (3 shown)                       
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Batch ID          ┃ Source    ┃ Status  ┃ Entries┃ Filename       ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ 123e4567-e89b-... │ NUBANK_CSV│COMPLETED│     42 │ nubank-2025...│
│ 234f5678-f90c-... │ NUBANK_CSV│COMPLETED│     35 │ nubank-2025...│
│ 345g6789-g01d-... │ NUBANK_CSV│ PENDING │      0 │ statement.csv  │
└───────────────────┴───────────┴─────────┴────────┴────────────────┘
```

### View Import Entries

```bash
fin import entries <batch-id> [OPTIONS]
```

**Options:**
- `--status, -s <STATUS>` - Filter by status (IMPORTED, MATCHED, POSTED)
- `--limit, -n <NUMBER>` - Number of entries to show (default: 100)

**Examples:**

```bash
# View all entries from a batch
fin import entries 123e4567-e89b-12d3-a456-426614174000

# View only imported (unmatched) entries
fin import entries <batch-id> --status IMPORTED

# Show first 20 entries
fin import entries <batch-id> --limit 20
```

**Output:**

```
Import Batch Details
Batch: 123e4567-e89b-12d3-a456-426614174000
Source: NUBANK_CSV
Status: COMPLETED
Total Entries: 42

                  Statement Entries (42 shown)                   
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━┓
┃ External ID     ┃ Date       ┃ Payee         ┃ Amount      ┃ Status ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━┩
│ SAL-001         │ 2025-10-01 │ Salary        │  5,000.00...│IMPORTED│
│ SUP-001         │ 2025-10-02 │ Supermarket   │   -250.50...│IMPORTED│
│ COF-001         │ 2025-10-03 │ Coffee Shop   │    -12.00...│IMPORTED│
└─────────────────┴────────────┴───────────────┴─────────────┴────────┘
```

## Workflow

The typical workflow for importing bank statements:

### 1. Import

Import your bank statement CSV:

```bash
fin import nubank ~/Downloads/statement.csv --account "Assets:Nubank"
```

This creates:
- **Import Batch** with status PENDING → COMPLETED
- **Statement Entries** with status IMPORTED

### 2. Review

Review the imported entries:

```bash
fin import entries <batch-id>
```

Verify:
- ✓ All transactions are present
- ✓ Amounts are correct
- ✓ Dates are accurate
- ✓ No duplicates

### 3. Match (Coming Soon)

Match statement entries to accounts:

```bash
# Automatic matching based on rules
fin match auto --batch <batch-id>

# Manual matching
fin match manual <entry-id> --debit "Expenses:Food" --credit "Assets:Nubank"
```

This updates entries from IMPORTED → MATCHED.

### 4. Post (Coming Soon)

Post matched entries as transactions:

```bash
fin post batch <batch-id>
```

This:
- Creates transactions in your ledger
- Updates entries from MATCHED → POSTED
- Links entries to transaction IDs

## Deduplication

Finlite automatically prevents duplicate imports using **SHA256 file hashing**.

### How it Works

1. When you import a file, Finlite calculates its SHA256 hash
2. This hash is stored in the import batch
3. On subsequent imports, the hash is checked first
4. If a match is found, the import is rejected

### Example

```bash
# First import - SUCCESS
$ fin import nubank statement.csv
✓ Import successful! Batch ID: 123e4567...

# Second import of same file - REJECTED
$ fin import nubank statement.csv
✗ Error: File already imported as batch 123e4567-e89b-12d3-a456-426614174000
```

### Why SHA256?

SHA256 provides strong duplicate detection even if:
- File is renamed
- File is moved to a different location
- File metadata (timestamps) is modified

**Note:** If the file *content* changes (even by one byte), it will be treated as a new file.

## Entry Status Flow

Statement entries progress through three states:

```
IMPORTED → MATCHED → POSTED
```

- **IMPORTED**: Entry was imported but not yet matched to accounts
- **MATCHED**: Entry has been matched to debit/credit accounts
- **POSTED**: Entry has been posted as a transaction in the ledger

You can filter by status when viewing entries:

```bash
fin import entries <batch-id> --status IMPORTED  # Unprocessed entries
fin import entries <batch-id> --status MATCHED   # Ready to post
fin import entries <batch-id> --status POSTED    # Already posted
```

## Troubleshooting

### Import Failed: "Invalid date format"

**Problem:** CSV contains dates in unexpected format.

**Solution:** Finlite supports:
- ISO format: `YYYY-MM-DD` (e.g., `2025-10-01`)
- Brazilian format: `DD/MM/YYYY` (e.g., `01/10/2025`)

Ensure your CSV uses one of these formats.

### Import Failed: "Invalid amount"

**Problem:** Amount column contains non-numeric data.

**Solution:** 
- Use decimal point (not comma): `100.50` ✓ not `100,50` ✗
- Negative amounts for debits: `-50.00`
- Remove currency symbols: `100.00` ✓ not `R$ 100,00` ✗

### Import Failed: "File not found"

**Problem:** File path is incorrect or file doesn't exist.

**Solution:**
- Use absolute paths: `/Users/you/Downloads/file.csv`
- Or relative paths from current directory: `./file.csv`
- Check file permissions (must be readable)

### Duplicate Import Error

**Problem:** File was already imported.

**Solution:**
- This is intentional! Finlite prevents duplicate imports.
- To reimport, you must:
  1. Delete or reverse the original batch (coming soon)
  2. Or modify the file content (not recommended)

### Missing Columns

**Problem:** CSV doesn't have required columns.

**Solution:** Ensure your CSV has at minimum:
- Date column: `date` or `data`
- Description: `description` or `descrição`  
- Amount: `amount` or `valor`

Finlite supports various column name aliases (case-insensitive).

## Best Practices

### 1. Regular Imports

Import statements regularly (weekly or monthly) to:
- Keep your records up-to-date
- Catch errors early
- Simplify matching

### 2. Use Account Hints

Specify an account hint when importing:

```bash
fin import nubank statement.csv --account "Assets:Nubank:Checking"
```

This helps with:
- Automatic matching (future feature)
- Manual matching workflows
- Understanding entry origin

### 3. Review Before Matching

Always review imported entries before matching/posting:

```bash
fin import entries <batch-id>
```

Look for:
- ✓ Unexpected transactions
- ✓ Incorrect amounts
- ✓ Duplicate entries (within same file)

### 4. Keep Original Files

Keep your original CSV/OFX files for audit purposes. The SHA256 hash proves file integrity.

### 5. Batch Organization

Use descriptive filenames:
- ✓ `nubank-checking-2025-10.csv`
- ✓ `chase-credit-card-oct-2025.csv`
- ✗ `statement.csv`
- ✗ `download (3).csv`

## Advanced Topics

### Custom CSV Formats

If your bank uses a different CSV format, you can:

1. Manually rename columns to match expected names
2. Or create a custom import use case (requires coding)

Example transformation:

```bash
# Original bank CSV
TXN_DATE,DESCRIPTION,DEBIT,CREDIT

# Rename to Finlite format
date,description,amount
```

### Bulk Operations (Coming Soon)

Future features:
- Bulk match: Match all entries in a batch
- Bulk post: Post all matched entries
- Bulk reverse: Reverse an entire import batch

### API Integration (Coming Soon)

Future features:
- Direct API connections to banks
- Automatic periodic imports
- Real-time transaction syncing

## See Also

- [Account Management](./accounts.md)
- [Transaction Recording](./transactions.md)
- [Rules Engine](./rules.md) (coming soon)
- [Reports](./reports.md) (coming soon)
