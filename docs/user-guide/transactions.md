# Transactions

Transactions in Finlite record financial events using double-entry bookkeeping. Each transaction must have at least two postings and sum to zero.

## Create Transaction (interactive)

```bash
fin transactions create --description "Salary" --date 2025-10-01
```

Follow prompts to add postings (account code + amount).

## List Transactions

```bash
fin transactions list --account CHECKING --start 2025-10-01 --end 2025-10-31
```

## Best Practices

- Use clear descriptions and `--payee` where applicable
- Ensure transactions balance before confirming
- Use splitting for transactions that hit multiple categories

See: [Double-Entry Guide](../user-guide/double-entry.md) and [CLI Reference](../user-guide/cli-reference.md).