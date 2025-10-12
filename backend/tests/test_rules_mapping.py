from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from finlite.rules.mapping import MapRule, find_matching_rule


def test_find_matching_rule_respects_type_thresholds_and_hours() -> None:
    rules = [
        MapRule(pattern="uber", account="Expenses:Transport", type="expense"),
        MapRule(pattern="bonus", account="Income:Bonus", type="income", min_amount=100.0),
        MapRule(
            pattern="café",
            account="Expenses:Coffee",
            type="expense",
            hour_start=6,
            hour_end=10,
        ),
    ]

    match = find_matching_rule(rules, "Uber viagem", is_expense=True, amount=Decimal("-20.00"))
    assert match is not None
    _, rule = match
    assert rule.account == "Expenses:Transport"

    assert (
        find_matching_rule(rules, "bonus recebido", is_expense=False, amount=Decimal("80")) is None
    )

    match = find_matching_rule(rules, "bonus recebido", is_expense=False, amount=Decimal("120"))
    assert match is not None
    assert match[1].account == "Income:Bonus"

    morning = datetime(2025, 8, 21, 8, 0, tzinfo=UTC)
    match = find_matching_rule(rules, "Café da manhã", is_expense=True, occurred_at=morning)
    assert match is not None
    assert match[1].account == "Expenses:Coffee"

    night = datetime(2025, 8, 21, 20, 0, tzinfo=UTC)
    assert find_matching_rule(rules, "Café da noite", is_expense=True, occurred_at=night) is None
