"""Basic OFX importer.

This parser is intentionally minimal and SGML-tolerant:
- Extracts transactions under STMTTRN blocks
- Supports fields: DTPOSTED, TRNAMT, FITID, NAME, MEMO, and optional CURRENCY
- Falls back to header-level CURDEF for currency

Notes:
- OFX dates (DTPOSTED) are parsed using the first 14 digits (YYYYMMDDHHMMSS).
  Timezone offsets are ignored and timestamps are stored as UTC.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from finlite.db.models import ImportBatch, StatementEntry
from finlite.ingest.utils import parse_amount, sha256_file

_TAG_VAL_RE = re.compile(r"<([A-Z0-9_]+)>([^<\n\r]*)")


def _parse_ofx_datetime(value: str) -> datetime:
    # OFX typically: YYYYMMDDHHMMSS[.sss][Z|[+/-]hhmm]
    m = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", value)
    if not m:
        # Fallback to current time to avoid crashing; caller may override
        return datetime.now(UTC)
    year, mon, day, hh, mm, ss = map(int, m.groups())
    return datetime(year, mon, day, hh, mm, ss, tzinfo=UTC)


def _read_text(path: Path) -> str:
    # Try utf-8, fallback to latin-1
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")


def _extract_blocks(ofx_text: str) -> list[dict[str, str]]:
    """Extract STMTTRN blocks into dicts of tag->value."""
    blocks: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    header_currency: str | None = None
    for raw in ofx_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Header-level currency
        if header_currency is None and line.upper().startswith("<CURDEF>"):
            value = line.split(">", 1)[-1]
            header_currency = value.split("<", 1)[0].strip().upper()

        if line.upper().startswith("<STMTTRN>"):
            current = {}
            continue
        if current is not None and line.upper().startswith("</STMTTRN>"):
            if header_currency and "CURRENCY" not in current:
                current["CURRENCY"] = header_currency
            blocks.append(current)
            current = None
            continue
        if current is not None:
            m = _TAG_VAL_RE.match(line)
            if m:
                tag = m.group(1).upper()
                val = m.group(2).strip()
                current[tag] = val
    return blocks


def import_ofx(
    session: Session,
    path: Path,
    default_currency: str,
    account_hint: str | None = None,
) -> ImportBatch:
    source = "ofx"
    digest = sha256_file(path)

    # Guard against duplicate re-import of the same file name (source+external_id unique)
    existing = session.scalar(
        select(ImportBatch)
        .where(ImportBatch.source == source, ImportBatch.external_id == path.name)
        .limit(1)
    )
    if existing is not None:
        raise RuntimeError(f"Batch already imported for {path.name}")

    text = _read_text(path)
    blocks = _extract_blocks(text)

    # Create batch
    batch = ImportBatch(source=source, external_id=path.name, file_sha256=digest, extra={})
    session.add(batch)
    session.flush()

    for idx, b in enumerate(blocks, start=1):
        dt = b.get("DTPOSTED") or ""
        occurred_at = _parse_ofx_datetime(dt) if dt else datetime.now(UTC)
        trnamt = b.get("TRNAMT") or "0"
        try:
            amount = Decimal(trnamt)
        except InvalidOperation:
            amount = parse_amount(trnamt)
        name = b.get("NAME") or ""
        memo = b.get("MEMO") or ""
        desc = (name + (" - " if name and memo else "") + memo).strip()
        ext_id = b.get("FITID") or f"{path.name}:row:{idx}"
        currency = (b.get("CURRENCY") or default_currency).upper()

        entry = StatementEntry(
            batch_id=batch.id,
            external_id=ext_id,
            payee=name or None,
            memo=desc or None,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            extra={"account_hint": account_hint} if account_hint else {},
        )
        session.add(entry)

    session.flush()
    return batch
