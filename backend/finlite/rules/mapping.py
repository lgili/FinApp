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
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from finlite.config import Settings

RuleType = Literal["expense", "income"]


@dataclass(slots=True)
class MapRule:
    pattern: str
    account: str
    type: RuleType


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
            rules.append(MapRule(pattern=pattern, account=account, type=rule_type))
        return rules
    except Exception:
        return []


def save_rules(settings: Settings, rules: Iterable[MapRule]) -> None:
    p = _map_path(settings)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {"rules": [rule.__dict__ for rule in rules]}
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_rule(settings: Settings, rule: MapRule) -> list[MapRule]:
    rules = load_rules(settings)
    rules.append(rule)
    save_rules(settings, rules)
    return rules


def match_account(settings: Settings, text: str, is_expense: bool) -> str | None:
    rules = load_rules(settings)
    t = text.lower()
    desired_type: RuleType = "expense" if is_expense else "income"
    for rule in rules:
        if rule.type != desired_type:
            continue
        if rule.pattern.lower() in t:
            return rule.account
    return None
