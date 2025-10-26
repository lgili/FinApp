"""Repository interface for card statements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Iterable, Optional
from uuid import UUID

from finlite.domain.entities.card_statement import CardStatementRecord, StatementStatus


class ICardStatementRepository(ABC):
    """Abstract repository contract for persisted credit card statements."""

    @abstractmethod
    def save(self, statement: CardStatementRecord) -> CardStatementRecord:
        """Persist or update a statement."""

    @abstractmethod
    def find_by_period(
        self,
        card_account_id: UUID,
        period_start: date,
        period_end: date,
    ) -> Optional[CardStatementRecord]:
        """Fetch statement for a given card and period if present."""

    @abstractmethod
    def list_open(self, card_account_id: UUID) -> Iterable[CardStatementRecord]:
        """Return all open statements for the card."""

    @abstractmethod
    def mark_paid(self, statement_id: UUID) -> None:
        """Mark a statement as paid."""
