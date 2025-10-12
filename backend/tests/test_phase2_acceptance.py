from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy import func, select
from typer.testing import CliRunner

from finlite.cli.app import app
from finlite.config import Settings
from finlite.db.models import StatementEntry
from finlite.db.session import session_scope

DATASET_TOTAL_RECORDS = 10
MIN_RULE_COVERAGE = 0.9


def _dataset_path() -> Path:
    return Path(__file__).resolve().parents[2] / "examples" / "banking" / "phase2_rules_dataset.csv"


def _import_dataset(runner: CliRunner, dataset: Path) -> None:
    result = runner.invoke(
        app,
        [
            "import",
            "nubank",
            str(dataset),
            "--account",
            "Assets:Bank:Nubank",
        ],
    )
    assert result.exit_code == 0, result.stdout


def _add_baseline_rules(runner: CliRunner) -> None:
    rules = [
        ("salário", "Income:Salary", "income", []),
        ("uber", "Expenses:Transport", "expense", ["--regex"]),
        ("ifood", "Expenses:FoodDelivery", "expense", []),
        ("spotify", "Expenses:Subscriptions", "expense", []),
        ("supermercado", "Expenses:Groceries", "expense", []),
        ("farmácia", "Expenses:Health", "expense", []),
    ]
    for pattern, account, kind, extra in rules:
        args = [
            "rules",
            "add",
            pattern,
            account,
            "--type",
            kind,
            *extra,
        ]
        result = runner.invoke(app, args)
        assert result.exit_code == 0, result.stdout


def _apply_rules(runner: CliRunner) -> None:
    result = runner.invoke(app, ["rules", "apply"])
    assert result.exit_code == 0, result.stdout


def _coverage(settings: Settings) -> tuple[int, int]:
    with session_scope(settings) as session:
        total = session.scalar(select(func.count()).select_from(StatementEntry)) or 0
        suggested = (
            session.scalar(
                select(func.count())
                .select_from(StatementEntry)
                .where(StatementEntry.suggested_account_id.is_not(None))
            )
            or 0
        )
    return total, suggested


def test_phase2_rules_dataset_covers_ninety_percent(
    cli_runner: tuple[CliRunner, Settings], tmp_path: Path
) -> None:
    runner, settings = cli_runner

    result = runner.invoke(app, ["init-db"])
    assert result.exit_code == 0, result.stdout

    dataset_src = _dataset_path()
    dataset_copy = tmp_path / dataset_src.name
    shutil.copyfile(dataset_src, dataset_copy)

    _import_dataset(runner, dataset_copy)
    _add_baseline_rules(runner)
    _apply_rules(runner)

    total, suggested = _coverage(settings)
    assert total == DATASET_TOTAL_RECORDS
    assert suggested / total >= MIN_RULE_COVERAGE

    # Reimporting the same file should not create duplicates and should fail fast.
    rerun = runner.invoke(
        app,
        [
            "import",
            "nubank",
            str(dataset_copy),
            "--account",
            "Assets:Bank:Nubank",
        ],
    )
    assert rerun.exit_code != 0
    total_after, suggested_after = _coverage(settings)
    assert total_after == total
    assert suggested_after == suggested
