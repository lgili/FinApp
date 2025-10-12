from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from typer.testing import CliRunner

from finlite.cli.app import app
from finlite.config import Settings
from finlite.db.models import ImportBatch, StatementEntry, StatementStatus
from finlite.db.session import session_scope
from finlite.rules.mapping import load_rules, match_account


def _seed_entries(settings: Settings) -> None:
    with session_scope(settings) as session:
        batch = ImportBatch(source="test", external_id="batch-1", file_sha256="hash", extra={})
        session.add(batch)
        session.flush()

        session.add(
            StatementEntry(
                batch_id=batch.id,
                external_id="txn-1",
                memo="Uber viagem noite",
                payee="Uber",
                amount=Decimal("-45.10"),
                currency="BRL",
                occurred_at=datetime(2025, 8, 20, 22, 30, tzinfo=UTC),
                status=StatementStatus.IMPORTED,
                extra={},
            )
        )
        session.add(
            StatementEntry(
                batch_id=batch.id,
                external_id="txn-2",
                memo="Depósito amigo",
                payee="Fulano",
                amount=Decimal("150.00"),
                currency="BRL",
                occurred_at=datetime(2025, 8, 21, 10, 0, tzinfo=UTC),
                status=StatementStatus.IMPORTED,
                extra={},
            )
        )


def test_rules_apply_dry_run_and_stats(cli_runner: tuple[CliRunner, Settings]) -> None:
    runner, settings = cli_runner

    result = runner.invoke(app, ["init-db"])
    assert result.exit_code == 0, result.stdout

    _seed_entries(settings)

    add_rule = runner.invoke(
        app,
        [
            "rules",
            "add",
            "uber",
            "Expenses:Transport",
            "--type",
            "expense",
            "--regex",
        ],
    )
    assert add_rule.exit_code == 0, add_rule.stdout

    rules_path = settings.data_dir / "category_map.json"
    assert rules_path.exists()
    assert rules_path.read_text(encoding="utf-8")

    rules = load_rules(settings)
    assert len(rules) == 1
    assert rules[0].pattern == "uber"
    assert rules[0].regex is True

    assert match_account(settings, "Uber viagem noite", is_expense=True) == "Expenses:Transport"

    dry_run = runner.invoke(app, ["rules", "apply", "--dry-run"])
    assert dry_run.exit_code == 0, dry_run.stdout
    assert "Rules Apply Preview" in dry_run.stdout
    assert "Uber viagem noite" in dry_run.stdout
    assert "Would match 1 entries" in dry_run.stdout

    apply_result = runner.invoke(app, ["rules", "apply"])
    assert apply_result.exit_code == 0, apply_result.stdout
    assert "Applied rules to 1 entries" in apply_result.stdout

    with session_scope(settings) as session:
        entries = session.scalars(select(StatementEntry).order_by(StatementEntry.external_id)).all()
        first, second = entries
        assert first.status == StatementStatus.MATCHED
        assert first.suggested_account_id is not None
        assert second.status == StatementStatus.IMPORTED
        assert second.suggested_account_id is None

    stats_result = runner.invoke(app, ["rules", "stats"])
    assert stats_result.exit_code == 0, stats_result.stdout
    assert "Statement Entries Overview" in stats_result.stdout
    assert "Total" in stats_result.stdout
    assert "Unmatched" in stats_result.stdout
    assert "Rule Coverage" in stats_result.stdout
    assert "Expenses:Transport" in stats_result.stdout
    assert "Entries covered by rules" in stats_result.stdout
