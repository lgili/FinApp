"""Simple description→account mapping stored as JSON in data_dir.

Schema example (category_map.json):
{
  "rules": [
    {"pattern": "mercado", "account": "Expenses:Groceries", "type": "expense"},
    {"pattern": "salário", "account": "Income:Salary", "type": "income"}
  ]
}
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

from finlite.config import Settings

RuleType = Literal["expense", "income"]


@dataclass(slots=True)
class MapRule:
    pattern: str
    account: str
    type: RuleType
    regex: bool = False
    min_amount: float | None = None
    max_amount: float | None = None
    hour_start: int | None = None
    hour_end: int | None = None


def _map_path(settings: Settings) -> Path:
    return settings.data_dir / "category_map.json"


def load_rules(settings: Settings) -> list[MapRule]:
    p = _map_path(settings)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        rules_raw = data.get("rules", [])
        rules: list[MapRule] = []

        def _to_rule_type(s: str) -> RuleType:
            return "expense" if s == "expense" else "income"

        for item in rules_raw:
            pattern = str(item.get("pattern", ""))
            account = str(item.get("account", ""))
            type_raw = str(item.get("type", "expense")).lower()
            if not pattern or not account or type_raw not in ("expense", "income"):
                continue
            rule_type: RuleType = _to_rule_type(type_raw)
            rules.append(
                MapRule(
                    pattern=pattern,
                    account=account,
                    type=rule_type,
                    regex=bool(item.get("regex", False)),
                    min_amount=(
                        float(item["min_amount"]) if item.get("min_amount") is not None else None
                    ),
                    max_amount=(
                        float(item["max_amount"]) if item.get("max_amount") is not None else None
                    ),
                    hour_start=(
                        int(item["hour_start"]) if item.get("hour_start") is not None else None
                    ),
                    hour_end=(int(item["hour_end"]) if item.get("hour_end") is not None else None),
                )
            )
        return rules
    except Exception:
        return []


def save_rules(settings: Settings, rules: Iterable[MapRule]) -> None:
    p = _map_path(settings)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {"rules": [asdict(rule) for rule in rules]}
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_rule(settings: Settings, rule: MapRule) -> list[MapRule]:
    rules = load_rules(settings)
    rules.append(rule)
    save_rules(settings, rules)
    return rules


def match_account(
    settings: Settings,
    text: str,
    is_expense: bool,
    *,
    amount: Decimal | None = None,
    occurred_at: datetime | None = None,
) -> str | None:
    rules = load_rules(settings)
    match = find_matching_rule(
        rules,
        text,
        is_expense=is_expense,
        amount=amount,
        occurred_at=occurred_at,
    )
    if match is None:
        return None
    _, rule = match
    return rule.account


def find_matching_rule(
    rules: Sequence[MapRule],
    text: str,
    is_expense: bool,
    *,
    amount: Decimal | None = None,
    occurred_at: datetime | None = None,
) -> tuple[int, MapRule] | None:
    """Return the first rule that matches the entry text and metadata."""

    normalized = text.lower()
    desired_type: RuleType = "expense" if is_expense else "income"
    for idx, rule in enumerate(rules):
        if rule.type != desired_type:
            continue

        matched = False
        if rule.regex:
            try:
                if re.search(rule.pattern, text, re.IGNORECASE):
                    matched = True
            except re.error:
                matched = rule.pattern.lower() in normalized
        else:
            matched = rule.pattern.lower() in normalized

        if not matched:
            continue

        if amount is not None:
            abs_amt = abs(amount)
            if rule.min_amount is not None and abs_amt < Decimal(str(rule.min_amount)):
                continue
            if rule.max_amount is not None and abs_amt > Decimal(str(rule.max_amount)):
                continue

        if occurred_at is not None and rule.hour_start is not None and rule.hour_end is not None:
            hour = occurred_at.hour
            if not (rule.hour_start <= hour <= rule.hour_end):
                continue

        return idx, rule

    return None
