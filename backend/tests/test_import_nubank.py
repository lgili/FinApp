from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from finlite.db.models import StatementEntry
from finlite.ingest.nubank_csv import import_nubank_csv

CSV_SAMPLE = dedent(
    """
    Data,Descrição,Valor
    01/08/2025,Compra Mercado,-123,45
    15/08/2025,Salário,1000,00
    """
).strip()


def _write_csv(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_import_nubank_csv_basic(session: Session, tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "nubank.csv", CSV_SAMPLE)
    batch = import_nubank_csv(session, csv_path, default_currency="BRL")
    session.flush()

    assert batch.id is not None
    entries = session.scalars(
        select(StatementEntry).where(StatementEntry.batch_id == batch.id)
    ).all()
    EXPECT = 2
    assert len(entries) == EXPECT
    amounts = sorted(e.amount for e in entries)
    assert str(amounts[0]) in {"-123.45", "-123.4500"}
    assert str(amounts[1]) in {"1000", "1000.0000"}


def test_import_nubank_csv_reimport_raises_on_duplicate(session: Session, tmp_path: Path) -> None:
    csv_path = _write_csv(tmp_path, "nubank.csv", CSV_SAMPLE)
    import_nubank_csv(session, csv_path, default_currency="BRL")
    session.flush()

    with pytest.raises(RuntimeError):
        import_nubank_csv(session, csv_path, default_currency="BRL")
