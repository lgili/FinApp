# Account Management

This page documents account-related operations in Finlite. Use the CLI to create, list, and inspect accounts.

## Create Account

Use `fin accounts create` to create a new account. See the CLI Reference for full options.

```bash
fin accounts create --code "CASH" --name "Cash" --type ASSET
```

## List Accounts

```bash
fin accounts list
```

## Inspect Balance

```bash
fin accounts balance CASH
```

## Notes

- Accounts belong to one of five types: ASSET, LIABILITY, EQUITY, INCOME, EXPENSE.
- Use hierarchical `--parent` when creating nested accounts.

See also: [CLI Reference](../user-guide/cli-reference.md) — for full command usage.