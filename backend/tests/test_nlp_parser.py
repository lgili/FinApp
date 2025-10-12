from __future__ import annotations

import pytest

from finlite.nlp.ask_agent import parse_intent
from finlite.nlp.intents import (
    ImportFileIntent,
    ListTransactionsIntent,
    MakeRuleIntent,
    PostPendingIntent,
    ReportCashflowIntent,
    ReportCategoryIntent,
)


@pytest.mark.parametrize(
    "query, expected_type",
    [
        ('Importe ./extrato.csv do nubank na conta "Assets:Bank:Nubank"', ImportFileIntent),
        ('Quanto gastei com "Expenses:Food" em 2025-09?', ReportCategoryIntent),
        ('Mostrar transações com "Uber"', ListTransactionsIntent),
        ('Cria regra "Uber" -> "Expenses:Transport" regex', MakeRuleIntent),
        ("Gerar cashflow mês 2025-08", ReportCashflowIntent),
        ("Posta todas as pendências", PostPendingIntent),
    ],
)
def test_rule_parser_recognises_queries(query: str, expected_type: type) -> None:
    result = parse_intent(query)
    assert isinstance(result.intent, expected_type)

    # Spot-check fields for more complex intents
    intent = result.intent
    if isinstance(intent, ImportFileIntent):
        assert intent.source == "nubank"
    if isinstance(intent, ReportCategoryIntent):
        assert intent.category == "Expenses:Food"
    if isinstance(intent, ListTransactionsIntent):
        assert intent.text == "Uber"
    if isinstance(intent, MakeRuleIntent):
        assert intent.regex is True
        assert intent.account == "Expenses:Transport"
