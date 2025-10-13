# Logging & Debugging

Finlite uses structured logging (structlog). This page explains logging modes and how to interpret logs.

## CLI Flags

- `--debug` — human-friendly, colorized output for development
- `--json-logs` — JSON structured logs for aggregation

## Examples

Debug (human-readable):

```bash
fin --debug accounts create -c TEST -n Test -t ASSET
# 2025-10-12T14:30:00 [info] creating_account account_code=TEST
```

JSON mode:

```bash
fin --json-logs transactions list
# {"event":"transactions_listed","level":"info","timestamp":"...","count":10}
```

## Troubleshooting

- Increase verbosity with `--debug` to inspect internal steps
- Use `--json-logs` when piping logs to aggregation tools

For advanced observability, refer to `docs/architecture/event-bus.md` (event audit traces).