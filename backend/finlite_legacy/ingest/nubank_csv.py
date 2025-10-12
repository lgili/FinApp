"""Nubank CSV importer.

Expected columns (flexible header names are supported via aliases):
- date (Data)
- description (Descrição)
- amount (Valor)

Optional:
- id (Identificador/ID externo)
- currency (Moeda)
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from finlite.db.models import ImportBatch, StatementEntry
from finlite.ingest.utils import parse_amount, read_csv_rows, sha256_file

ALIASES = {
    "date": {"data", "date"},
    "description": {"descricao", "descrição", "description"},
    "amount": {"valor", "amount"},
    "id": {"id", "identificador", "external_id"},
    "currency": {"moeda", "currency"},
}


def _alias_lookup(row: dict[str, str], key: str) -> str | None:
    for candidate in ALIASES[key]:
        if candidate in row and row[candidate] != "":
            return row[candidate]
    return None


def import_nubank_csv(
    session: Session,
    path: Path,
    default_currency: str,
    account_hint: str | None = None,
) -> ImportBatch:
    source = "nubank_csv"
    digest = sha256_file(path)

    # Guard against duplicate re-import of the same file name (source+external_id unique)
    existing = session.scalar(
        select(ImportBatch)
        .where(ImportBatch.source == source, ImportBatch.external_id == path.name)
        .limit(1)
    )
    if existing is not None:
        raise RuntimeError(f"Batch already imported for {path.name}")

    # Create batch
    batch = ImportBatch(source=source, external_id=path.name, file_sha256=digest, extra={})
    session.add(batch)
    session.flush()

    for idx, row in enumerate(read_csv_rows(path), start=1):
        date_str = _alias_lookup(row, "date")
        desc = _alias_lookup(row, "description") or ""
        amt_str = _alias_lookup(row, "amount") or "0"
        # Build a stable external_id: filename + 1-based row index
        ext_id = _alias_lookup(row, "id") or f"{path.name}:row:{idx}"
        currency = (_alias_lookup(row, "currency") or default_currency).upper()

        try:
            occurred_at = datetime.fromisoformat(date_str or "")
        except Exception:
            # Try Brazilian dd/mm/yyyy
            occurred_at = datetime.strptime((date_str or ""), "%d/%m/%Y")
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)

        amount = parse_amount(amt_str)

        entry = StatementEntry(
            batch_id=batch.id,
            external_id=ext_id,
            payee=None,
            memo=desc,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            extra={"account_hint": account_hint} if account_hint else {},
        )
        session.add(entry)

    session.flush()

    return batch
