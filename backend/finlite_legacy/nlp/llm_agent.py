"""Helpers for running the optional Pydantic AI intent parser fallback."""

from __future__ import annotations

import importlib
import os
from functools import lru_cache
from typing import Any, Protocol, cast, get_args

from finlite.nlp.intents import Intent

LLM_INSTRUCTIONS = (
    "Você é um parser de comandos de finanças pessoais. "
    "Retorne SOMENTE JSON válido que cumpra um dos modelos Pydantic chamados Intent. "
    "Esses intents cobrem: import_file, report_cashflow, report_category, post_pending, "
    "list_transactions e make_rule. Nunca execute nada, apenas descreva a intenção."
)


class _IntentAgentResult(Protocol):
    data: Any


class _IntentAgent(Protocol):
    def run(self, query: str) -> _IntentAgentResult:
        """Execute the agent and return the raw result object."""


class _IntentAgentFactory(Protocol):
    def __call__(self, model: str, *, instructions: str, result_type: object) -> _IntentAgent:
        """Return a configured agent instance."""


@lru_cache(1)
def _load_agent_class() -> _IntentAgentFactory:
    """Return the ``pydantic_ai.Agent`` factory, importing it lazily."""

    try:
        module = importlib.import_module("pydantic_ai")
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "pydantic_ai is not installed. Install finlite[ai] to enable NL fallback."
        ) from exc

    try:
        agent_cls = module.Agent
    except AttributeError as exc:  # pragma: no cover - defensive
        raise RuntimeError("pydantic_ai.Agent not found; upgrade pydantic-ai.") from exc
    return cast(_IntentAgentFactory, agent_cls)


def build_intent_agent(model: str | None = None) -> _IntentAgent:
    """Instantiate and return a configured Pydantic AI agent for intents."""

    agent_cls = _load_agent_class()
    selected_model = model or os.environ.get("FINLITE_LLM_MODEL", "openai:gpt-4o-mini")
    return agent_cls(selected_model, instructions=LLM_INSTRUCTIONS, result_type=Intent)


def run_intent_agent(query: str, *, model: str | None = None) -> Intent:
    """Execute the LLM fallback and return a validated ``Intent`` instance."""

    agent = build_intent_agent(model=model)
    result = agent.run(query)
    intent_data = getattr(result, "data", None)
    if intent_data is None:
        raise ValueError("LLM did not return a valid intent payload.")
    if not isinstance(intent_data, get_args(Intent)):
        # Ensure Pydantic returned an instance compatible with our union
        raise ValueError("LLM returned an unknown intent type.")
    return cast(Intent, intent_data)


def clear_intent_agent_cache() -> None:
    """Reset the cached agent factory (mainly for testing)."""

    _load_agent_class.cache_clear()
