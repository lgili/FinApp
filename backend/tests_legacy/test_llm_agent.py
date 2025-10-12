from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from finlite.nlp.intents import ImportFileIntent
from finlite.nlp.llm_agent import (
    build_intent_agent,
    clear_intent_agent_cache,
    run_intent_agent,
)


@pytest.fixture(autouse=True)
def reset_agent_cache() -> None:
    clear_intent_agent_cache()


def test_build_intent_agent_raises_when_dependency_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(os.environ, "FINLITE_LLM_MODEL", "test-model")

    with (
        patch("importlib.import_module", side_effect=ModuleNotFoundError),
        pytest.raises(RuntimeError, match="pydantic_ai is not installed"),
    ):
        build_intent_agent()


def test_run_intent_agent_returns_valid_intent() -> None:
    mock_agent_instance = MagicMock()
    mock_intent = ImportFileIntent(
        source="nubank",
        path="/tmp/file.csv",
        account="Assets:Bank:Nubank",
        auto=True,
    )
    mock_result = MagicMock(data=mock_intent)
    mock_agent_instance.run.return_value = mock_result

    mock_agent_cls = MagicMock(return_value=mock_agent_instance)

    with patch("importlib.import_module", return_value=MagicMock(Agent=mock_agent_cls)):
        result = run_intent_agent("teste")

    mock_agent_cls.assert_called_once()
    mock_agent_instance.run.assert_called_once_with("teste")
    assert result is mock_intent
