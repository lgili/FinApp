"""
Pay Card Use Case - Registra pagamento de fatura de cartão de crédito.

Responsabilidade: Criar transaction de pagamento de cartão (transferência de ASSET para LIABILITY).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from finlite.domain.entities.transaction import Transaction
from finlite.domain.repositories.account_repository import IAccountRepository
from finlite.domain.repositories.transaction_repository import ITransactionRepository
from finlite.domain.value_objects.account_type import AccountType
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting
from finlite.infrastructure.persistence.unit_of_work import UnitOfWork


@dataclass
class PayCardCommand:
    """Command para pagar fatura de cartão."""

    card_account_code: str  # ex: "Liabilities:CreditCard:Nubank"
    payment_account_code: str  # ex: "Assets:Checking"
    amount: Decimal
    currency: str
    date: datetime
    description: str = "Credit card payment"


@dataclass
class PayCardResult:
    """Resultado do pagamento de cartão."""

    transaction_id: UUID
    card_account_code: str
    payment_account_code: str
    amount: Decimal
    currency: str
    date: datetime


class PayCardUseCase:
    """
    Use case para registrar pagamento de fatura de cartão de crédito.

    Em contabilidade de partida dobrada:
    - Pagamento DEBITA o cartão (LIABILITY) - reduz dívida
    - Pagamento CREDITA a conta bancária (ASSET) - sai dinheiro

    Transação gerada:
        Liabilities:CreditCard    +amount  (débito - reduz dívida)
        Assets:Checking           -amount  (crédito - sai dinheiro)

    Fluxo:
    1. Valida que card_account é LIABILITY
    2. Valida que payment_account é ASSET
    3. Cria transaction de pagamento
    4. Persiste no repositório

    Examples:
        >>> result = use_case.execute(
        ...     PayCardCommand(
        ...         card_account_code="Liabilities:CreditCard:Nubank",
        ...         payment_account_code="Assets:Checking",
        ...         amount=Decimal("1500.00"),
        ...         currency="BRL",
        ...         date=datetime(2025, 10, 5),
        ...         description="Payment of October invoice"
        ...     )
        ... )
        >>> print(f"Payment transaction: {result.transaction_id}")
    """

    def __init__(
        self,
        uow: UnitOfWork,
        account_repository: IAccountRepository,
        transaction_repository: ITransactionRepository,
    ):
        """
        Initialize use case.

        Args:
            uow: Unit of Work
            account_repository: Repository de contas
            transaction_repository: Repository de transactions
        """
        self.uow = uow
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository

    def execute(self, command: PayCardCommand) -> PayCardResult:
        """
        Executa pagamento de fatura.

        Args:
            command: Comando com parâmetros

        Returns:
            Resultado com ID da transaction criada

        Raises:
            ValueError: Se conta do cartão não for LIABILITY
            ValueError: Se conta de pagamento não for ASSET
            ValueError: Se contas não existirem
            ValueError: Se amount for <= 0
        """
        # Validar amount
        if command.amount <= 0:
            raise ValueError(f"Payment amount must be positive, got {command.amount}")

        with self.uow:
            # 1. Buscar conta do cartão
            card_account = self.account_repository.find_by_code(command.card_account_code)
            if not card_account:
                raise ValueError(
                    f"Card account not found: {command.card_account_code}"
                )

            # 2. Validar que é LIABILITY
            if card_account.account_type != AccountType.LIABILITY:
                raise ValueError(
                    f"Account {command.card_account_code} is not a LIABILITY account. "
                    f"Credit cards must be LIABILITY type."
                )

            # 3. Buscar conta de pagamento
            payment_account = self.account_repository.find_by_code(
                command.payment_account_code
            )
            if not payment_account:
                raise ValueError(
                    f"Payment account not found: {command.payment_account_code}"
                )

            # 4. Validar que é ASSET
            if payment_account.account_type != AccountType.ASSET:
                raise ValueError(
                    f"Account {command.payment_account_code} is not an ASSET account. "
                    f"Payment source must be ASSET type (checking, savings, etc)."
                )

            # 5. Criar money objects
            money = Money(amount=command.amount, currency=command.currency)

            # 6. Criar postings
            # Debita cartão (LIABILITY) - reduz dívida (valor positivo)
            # Credita conta bancária (ASSET) - sai dinheiro (valor negativo)
            postings = [
                Posting(account_id=card_account.id, amount=money),  # Débito LIABILITY
                Posting(account_id=payment_account.id, amount=-money),  # Crédito ASSET
            ]

            # 7. Criar transaction
            transaction = Transaction.create(
                date=command.date,
                description=command.description,
                postings=postings,
                tags=["card-payment"],
            )

            # 8. Persistir
            self.transaction_repository.add(transaction)
            self.uow.commit()

            return PayCardResult(
                transaction_id=transaction.id,
                card_account_code=card_account.code,
                payment_account_code=payment_account.code,
                amount=command.amount,
                currency=command.currency,
                date=command.date,
            )
