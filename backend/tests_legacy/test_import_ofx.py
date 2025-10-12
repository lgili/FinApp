from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from finlite.db.models import StatementEntry
from finlite.ingest.ofx import import_ofx

OFX_SAMPLE = dedent(
    """
    <OFX>
      <BANKMSGSRSV1>
        <STMTTRNRS>
          <STMTRS>
            <CURDEF>BRL</CURDEF>
            <BANKTRANLIST>
              <STMTTRN>
                <DTPOSTED>20250801120000</DTPOSTED>
                <TRNAMT>-50.25</TRNAMT>
                <FITID>txn-001</FITID>
                <NAME>Uber</NAME>
                <MEMO>Corrida</MEMO>
              </STMTTRN>
              <STMTTRN>
                <DTPOSTED>20250815150000</DTPOSTED>
                <TRNAMT>2500.00</TRNAMT>
                <FITID>txn-002</FITID>
                <NAME>Empresa</NAME>
                <MEMO>Salario</MEMO>
                <CURRENCY>USD</CURRENCY>
              </STMTTRN>
            </BANKTRANLIST>
          </STMTRS>
        </STMTTRNRS>
      </BANKMSGSRSV1>
    </OFX>
    """
).strip()


def _write_ofx(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


def test_import_ofx_basic(session: Session, tmp_path: Path) -> None:
    ofx_path = _write_ofx(tmp_path, "sample.ofx", OFX_SAMPLE)
    batch = import_ofx(session, ofx_path, default_currency="BRL")
    session.flush()

    entries = session.scalars(
        select(StatementEntry).where(StatementEntry.batch_id == batch.id)
    ).all()
    EXPECTED_COUNT = 2
    assert len(entries) == EXPECTED_COUNT

    first, second = entries
    assert str(first.amount) in {"-50.25", "-50.2500"}
    assert first.currency == "BRL"  # inherited from header
    assert first.memo == "Uber - Corrida"

    assert str(second.amount) in {"2500", "2500.0000"}
    assert second.currency == "USD"


def test_import_ofx_reimport_raises_on_duplicate(session: Session, tmp_path: Path) -> None:
    ofx_path = _write_ofx(tmp_path, "sample.ofx", OFX_SAMPLE)
    import_ofx(session, ofx_path, default_currency="BRL")
    session.flush()

    with pytest.raises(RuntimeError):
        import_ofx(session, ofx_path, default_currency="BRL")
