"""Pydantic models for natural language intents.

Intents map NL queries into typed actions that can be previewed and executed
safely by the CLI. Designed to be independent from any LLM backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class ImportFileIntent(BaseModel):
    kind: Literal["import_file"] = "import_file"
    source: Literal["nubank", "ofx"]
    path: str
    account: str
    auto: bool = True


class ReportCashflowIntent(BaseModel):
    kind: Literal["report_cashflow"] = "report_cashflow"
    month: str | None = None
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    category: str | None = None


class PostPendingIntent(BaseModel):
    kind: Literal["post_pending"] = "post_pending"
    auto: bool = True


class ReportCategoryIntent(BaseModel):
    kind: Literal["report_category"] = "report_category"
    category: str
    month: str | None = None
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None


class ListTransactionsIntent(BaseModel):
    kind: Literal["list_transactions"] = "list_transactions"
    text: str | None = None
    account: str | None = None
    limit: int = 20
    min_amount: float | None = None
    max_amount: float | None = None
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None


class MakeRuleIntent(BaseModel):
    kind: Literal["make_rule"] = "make_rule"
    pattern: str
    account: str
    type: Literal["expense", "income"]
    regex: bool = False
    min_amount: float | None = None
    max_amount: float | None = None
    hour_start: int | None = None
    hour_end: int | None = None


Intent = (
    ImportFileIntent
    | ReportCashflowIntent
    | PostPendingIntent
    | ReportCategoryIntent
    | ListTransactionsIntent
    | MakeRuleIntent
)


@dataclass(slots=True)
class IntentResult:
    """Result of parsing a NL prompt into an Intent.

    source indicates the mechanism used to obtain the intent (e.g., 'rule' or 'llm').
    """

    source: Literal["rule", "llm"]
    intent: Intent
