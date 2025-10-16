"""
Build Card Statement Use Case - Gera fatura de cartão de crédito.

Responsabilidade: Calcular fatura de cartão (LIABILITY account) para um período,
incluindo todas as compras e o total a pagar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from finlite.domain.repositories.account_repository import IAccountRepository
from finlite.domain.repositories.transaction_repository import ITransactionRepository
from finlite.domain.value_objects.account_type import AccountType
from finlite.infrastructure.persistence.unit_of_work import UnitOfWork


@dataclass
class BuildCardStatementCommand:
    """Command para gerar fatura de cartão."""

    card_account_code: str  # ex: "Liabilities:CreditCard:Nubank"
    from_date: datetime
    to_date: datetime
    currency: str = "BRL"


@dataclass
class StatementItem:
    """Item individual da fatura."""

    date: datetime
    description: str
    amount: Decimal  # Sempre positivo (valor da compra)
    category_code: str  # Conta de despesa (ex: "Expenses:Food")
    category_name: str
    transaction_id: UUID


@dataclass
class CardStatement:
    """Fatura de cartão de crédito."""

    card_account_code: str
    card_account_name: str
    from_date: datetime
    to_date: datetime
    currency: str

    # Items da fatura (compras)
    items: list[StatementItem]

    # Totais
    total_amount: Decimal  # Total das compras (sempre positivo)
    item_count: int

    # Saldo anterior (se houver)
    previous_balance: Decimal


class BuildCardStatementUseCase:
    """
    Use case para gerar fatura de cartão de crédito.

    Em contabilidade de partida dobrada:
    - Cartão de crédito é LIABILITY (passivo)
    - Compras CREDITAM o cartão (aumentam a dívida)
    - Pagamentos DEBITAM o cartão (reduzem a dívida)

    Fluxo:
    1. Valida que a conta é do tipo LIABILITY
    2. Busca todas as transactions que envolvem a conta do cartão
    3. Agrupa por tipo de posting (compras vs pagamentos)
    4. Gera fatura com detalhes das compras

    Examples:
        >>> result = use_case.execute(
        ...     BuildCardStatementCommand(
        ...         card_account_code="Liabilities:CreditCard:Nubank",
        ...         from_date=datetime(2025, 10, 1),
        ...         to_date=datetime(2025, 10, 31),
        ...         currency="BRL"
        ...     )
        ... )
        >>> print(f"Total: R$ {result.total_amount}")
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

    def execute(self, command: BuildCardStatementCommand) -> CardStatement:
        """
        Executa geração da fatura.

        Args:
            command: Comando com parâmetros

        Returns:
            Fatura de cartão

        Raises:
            ValueError: Se conta não for do tipo LIABILITY
            ValueError: Se conta não existir
        """
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

            # 3. Buscar transactions no período que envolvem o cartão
            all_transactions = self.transaction_repository.find_by_date_range(
                from_date=command.from_date,
                to_date=command.to_date,
            )

            # Filtrar apenas transactions que envolvem o cartão
            card_transactions = [
                txn for txn in all_transactions if txn.has_account(card_account.id)
            ]

            # 4. Buscar todas as contas (para lookup)
            all_accounts = self.account_repository.list_all()
            accounts_by_id = {acc.id: acc for acc in all_accounts}

            # 5. Processar items da fatura
            items: list[StatementItem] = []
            total_charges = Decimal("0")  # Total das compras

            for txn in card_transactions:
                # Buscar posting do cartão
                card_postings = txn.get_postings_for_account(card_account.id)

                for card_posting in card_postings:
                    # Em LIABILITY, crédito (negativo) aumenta dívida = compra
                    # Débito (positivo) reduz dívida = pagamento
                    if card_posting.is_credit():  # Compra
                        # Buscar a outra conta da transaction (categoria da despesa)
                        other_postings = [
                            p for p in txn.postings if p.account_id != card_account.id
                        ]

                        if other_postings:
                            # Pegar a primeira conta (normalmente é única)
                            other_posting = other_postings[0]
                            category_account = accounts_by_id.get(other_posting.account_id)

                            category_code = (
                                category_account.code
                                if category_account
                                else "Unknown"
                            )
                            category_name = (
                                category_account.name
                                if category_account
                                else "Unknown Category"
                            )
                        else:
                            category_code = "Unknown"
                            category_name = "Unknown Category"

                        # Valor da compra (sempre positivo na fatura)
                        charge_amount = abs(card_posting.amount.amount)

                        items.append(
                            StatementItem(
                                date=txn.date,
                                description=txn.description,
                                amount=charge_amount,
                                category_code=category_code,
                                category_name=category_name,
                                transaction_id=txn.id,
                            )
                        )

                        total_charges += charge_amount

            # 6. Ordenar items por data
            items.sort(key=lambda x: x.date)

            # 7. Calcular saldo anterior (transactions antes do período)
            # Para simplificar, vamos deixar como 0 por enquanto
            # No futuro, podemos calcular o saldo de todas as transactions anteriores
            previous_balance = Decimal("0")

            return CardStatement(
                card_account_code=card_account.code,
                card_account_name=card_account.name,
                from_date=command.from_date,
                to_date=command.to_date,
                currency=command.currency,
                items=items,
                total_amount=total_charges,
                item_count=len(items),
                previous_balance=previous_balance,
            )
