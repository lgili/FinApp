"""Agent entry for parsing NL queries to typed intents.

This module first tries a small grammar-based parser for common queries.
If that fails and pydantic_ai is available, it can attempt an LLM-backed parse.
The LLM path is optional and only used when the library is installed and
FINLITE_AI_ENABLE environment variable is set to a truthy value.
"""

from __future__ import annotations

import os
import re
from typing import Literal

from .intents import (
    ImportFileIntent,
    Intent,
    IntentResult,
    ListTransactionsIntent,
    MakeRuleIntent,
    PostPendingIntent,
    ReportCashflowIntent,
    ReportCategoryIntent,
)
from .llm_agent import run_intent_agent

_MONTH_RE = re.compile(r"(?P<year>\d{4})[-/](?P<month>0[1-9]|1[0-2])")
_QUOTED_RE = re.compile(r'"([^"]+)"|\'([^\']+)\'')
_MAIOR_QUE_RE = re.compile(r"maior que\s+([\d.,]+)")
_MENOR_QUE_RE = re.compile(r"menor que\s+([\d.,]+)")
_ARROW_RE = re.compile(r"(.+?)->(.+)")

_MIN_QUOTED_COMPONENTS = 2


def _extract_month(text: str) -> str | None:
    m = _MONTH_RE.search(text)
    if m:
        return f"{m.group('year')}-{m.group('month')}"
    return None


def _extract_quoted(text: str) -> list[str]:
    out: list[str] = []
    for m in _QUOTED_RE.finditer(text):
        out.append(m.group(1) or m.group(2) or "")
    return [s for s in out if s]


def _rule_parse(q: str) -> Intent | None:  # noqa: PLR0911, PLR0912, PLR0915
    t = q.lower().strip()

    # Import Nubank CSV
    if ("import" in t or "importe" in t) and "nubank" in t:
        # naive path extraction: first token ending with .csv
        path_match = re.search(r"\S+\.csv", q)
        if not path_match:
            return None
        path = path_match.group(0)
        # account hint: take a quoted value if present
        quoted = _extract_quoted(q)
        account = quoted[0] if quoted else "Assets:Bank:Nubank"
        return ImportFileIntent(source="nubank", path=path, account=account)

    # Post pending
    if any(k in t for k in ("post", "lança", "lanca")) and any(
        k in t for k in ("pending", "pendência", "pendencia", "tudo")
    ):
        return PostPendingIntent()

    # Cashflow report
    if any(k in t for k in ("cashflow", "relatório", "relatorio", "quanto gastei", "gastei")):
        month = _extract_month(t)
        quoted = _extract_quoted(q)
        category: str | None = None
        if quoted:
            category = quoted[0]
        elif "categoria" in t:
            after = t.split("categoria", 1)[-1].strip()
            if after:
                category = after.split()[0].strip(" :")
        if category:
            return ReportCategoryIntent(category=category, month=month)
        return ReportCashflowIntent(month=month)

    # List transactions
    if any(k in t for k in ("listar", "list", "mostrar", "exibir")) and "transa" in t:
        quoted = _extract_quoted(q)
        text_filter = quoted[0] if quoted else None
        account_filter = quoted[1] if quoted and len(quoted) > 1 else None
        min_amount = None
        max_amount = None
        maior = _MAIOR_QUE_RE.search(t)
        if maior:
            try:
                min_amount = float(maior.group(1).replace(".", "").replace(",", "."))
            except ValueError:
                min_amount = None
        menor = _MENOR_QUE_RE.search(t)
        if menor:
            try:
                max_amount = float(menor.group(1).replace(".", "").replace(",", "."))
            except ValueError:
                max_amount = None
        month = _extract_month(t)
        from_str = month + "-01" if month else None
        data: dict[str, object] = {
            "text": text_filter,
            "account": account_filter,
            "min_amount": min_amount,
            "max_amount": max_amount,
        }
        if from_str is not None:
            data["from"] = from_str
        return ListTransactionsIntent.model_validate(data)

    # Make rule
    if "regra" in t or "rule" in t:
        quoted = _extract_quoted(q)
        pattern: str | None = None
        matched_account: str | None = None
        if len(quoted) >= _MIN_QUOTED_COMPONENTS:
            pattern, matched_account = quoted[0], quoted[1]
        elif "->" in q:
            arrow = _ARROW_RE.search(q)
            if arrow:
                pattern = arrow.group(1).strip().strip("\"'")
                matched_account = arrow.group(2).strip().strip("\"'")
        if not pattern or not matched_account:
            return None
        rule_type: Literal["expense", "income"] = (
            "income" if any(word in t for word in ("receita", "income")) else "expense"
        )
        regex = "regex" in t
        min_amount = None
        max_amount = None
        maior = _MAIOR_QUE_RE.search(t)
        if maior:
            try:
                min_amount = float(maior.group(1).replace(".", "").replace(",", "."))
            except ValueError:
                min_amount = None
        menor = _MENOR_QUE_RE.search(t)
        if menor:
            try:
                max_amount = float(menor.group(1).replace(".", "").replace(",", "."))
            except ValueError:
                max_amount = None
        return MakeRuleIntent(
            pattern=pattern,
            account=matched_account,
            type=rule_type,
            regex=regex,
            min_amount=min_amount,
            max_amount=max_amount,
        )

    return None


def parse_intent(query: str) -> IntentResult:
    """Parse a NL query into a typed intent.

    Attempts a rule-based parse first, then falls back to pydantic_ai
    if available and enabled.
    """
    rule = _rule_parse(query)
    if rule is not None:
        return IntentResult(source="rule", intent=rule)

    # Optional LLM path
    if not os.environ.get("FINLITE_AI_ENABLE"):
        raise ValueError(
            "Could not parse query. Enable LLM with FINLITE_AI_ENABLE=1 or use supported phrases."
        )

    try:
        intent = run_intent_agent(query)
    except RuntimeError as exc:
        raise ValueError(f"LLM parsing requested but unavailable: {exc}") from exc
    except ValueError as exc:
        raise ValueError(f"LLM could not parse query: {exc}") from exc

    return IntentResult(source="llm", intent=intent)
