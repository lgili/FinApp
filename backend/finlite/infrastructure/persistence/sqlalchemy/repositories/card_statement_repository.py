"""SQLAlchemy implementation of card statement repository."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from finlite.domain.entities.card_statement import (
    CardStatementItem,
    CardStatementRecord,
    StatementStatus,
)
from finlite.domain.repositories.card_statement_repository import (
    ICardStatementRepository,
)
from finlite.infrastructure.persistence.sqlalchemy.mappers._uuid_helpers import (
    int_to_uuid,
    uuid_to_int,
)
from finlite.infrastructure.persistence.sqlalchemy.models import CardStatementModel


class SqlAlchemyCardStatementRepository(ICardStatementRepository):
    """SQLAlchemy-backed card statement repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, statement: CardStatementRecord) -> CardStatementRecord:
        model = self._session.get(CardStatementModel, statement.id)
        payload = self._to_model_payload(statement)
        if model is None:
            model = CardStatementModel(**payload)
            self._session.add(model)
        else:
            for key, value in payload.items():
                setattr(model, key, value)
        self._session.flush()
        return self._to_entity(model)

    def find_by_period(
        self,
        card_account_id: UUID,
        period_start: date,
        period_end: date,
    ) -> Optional[CardStatementRecord]:
        stmt = select(CardStatementModel).where(
            CardStatementModel.card_account_id == uuid_to_int(card_account_id),
            CardStatementModel.period_start == period_start,
            CardStatementModel.period_end == period_end,
        )
        model = self._session.scalar(stmt)
        if model is None:
            return None
        return self._to_entity(model)

    def list_open(self, card_account_id: UUID) -> Iterable[CardStatementRecord]:
        stmt = select(CardStatementModel).where(
            CardStatementModel.card_account_id == uuid_to_int(card_account_id),
            CardStatementModel.status == StatementStatus.OPEN.value,
        )
        return [self._to_entity(model) for model in self._session.scalars(stmt).all()]

    def mark_paid(self, statement_id: UUID) -> None:
        model = self._session.get(CardStatementModel, statement_id)
        if model is None:
            return
        model.status = StatementStatus.PAID.value
        model.updated_at = datetime.utcnow()
        self._session.flush()

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #

    def _to_model_payload(self, statement: CardStatementRecord) -> dict:
        return {
            "id": statement.id,
            "card_account_id": uuid_to_int(statement.card_account_id),
            "period_start": statement.period_start,
            "period_end": statement.period_end,
            "closing_day": statement.closing_day,
            "due_date": statement.due_date,
            "currency": statement.currency,
            "total_amount": statement.total_amount,
            "status": statement.status.value,
            "items": [self._item_to_dict(item) for item in statement.items],
            "created_at": statement.created_at,
            "updated_at": statement.updated_at,
        }

    def _to_entity(self, model: CardStatementModel) -> CardStatementRecord:
        return CardStatementRecord(
            id=model.id,
            card_account_id=int_to_uuid(model.card_account_id),
            period_start=model.period_start,
            period_end=model.period_end,
            closing_day=model.closing_day,
            due_date=model.due_date,
            currency=model.currency,
            total_amount=Decimal(model.total_amount),
            items=tuple(self._dict_to_item(item) for item in model.items),
            status=StatementStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _item_to_dict(item: CardStatementItem) -> dict:
        return {
            "transaction_id": str(item.transaction_id),
            "occurred_at": item.occurred_at.isoformat(),
            "description": item.description,
            "amount": str(item.amount),
            "currency": item.currency,
            "category_code": item.category_code,
            "category_name": item.category_name,
            "installment_number": item.installment_number,
            "installment_total": item.installment_total,
            "installment_key": item.installment_key,
        }

    @staticmethod
    def _dict_to_item(data: dict) -> CardStatementItem:
        return CardStatementItem(
            transaction_id=UUID(data["transaction_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            description=data["description"],
            amount=Decimal(data["amount"]),
            currency=data["currency"],
            category_code=data["category_code"],
            category_name=data["category_name"],
            installment_number=data.get("installment_number"),
            installment_total=data.get("installment_total"),
            installment_key=data.get("installment_key"),
        )
