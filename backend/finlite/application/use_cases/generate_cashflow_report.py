"""
Generate Cashflow Report Use Case - Gera relatório de fluxo de caixa.

Responsabilidade: Calcular entradas e saídas de dinheiro por período e categoria.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from finlite.domain.repositories.account_repository import IAccountRepository
from finlite.domain.repositories.transaction_repository import ITransactionRepository
from finlite.domain.value_objects.account_type import AccountType
from finlite.infrastructure.persistence.unit_of_work import UnitOfWork


@dataclass
class GenerateCashflowCommand:
    """Command para gerar relatório de cashflow."""

    from_date: datetime
    to_date: datetime
    account_code_filter: Optional[str] = None  # Filtrar por prefixo (ex: "Expenses:Food")
    currency: str = "USD"


@dataclass
class CashflowCategoryItem:
    """Item de categoria no cashflow."""

    account_code: str
    account_name: str
    amount: Decimal
    transaction_count: int


@dataclass
class CashflowReport:
    """Relatório de cashflow."""

    from_date: datetime
    to_date: datetime
    currency: str

    # Receitas (Income accounts)
    income_categories: list[CashflowCategoryItem]
    total_income: Decimal

    # Despesas (Expense accounts)
    expense_categories: list[CashflowCategoryItem]
    total_expenses: Decimal

    # Fluxo líquido
    net_cashflow: Decimal

    # Totais por conta Asset (opcional)
    asset_balances: list[CashflowCategoryItem]


class GenerateCashflowReportUseCase:
    """
    Use case para gerar relatório de fluxo de caixa.

    Fluxo:
    1. Busca todas as transactions no período
    2. Agrupa postings por conta
    3. Separa em Income, Expense, e Asset
    4. Calcula totais e fluxo líquido

    Examples:
        >>> from datetime import datetime
        >>> result = use_case.execute(
        ...     GenerateCashflowCommand(
        ...         from_date=datetime(2025, 10, 1),
        ...         to_date=datetime(2025, 10, 31),
        ...         currency="USD"
        ...     )
        ... )
        >>> print(f"Net Cashflow: {result.net_cashflow}")
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

    def execute(self, command: GenerateCashflowCommand) -> CashflowReport:
        """
        Executa geração do relatório.

        Args:
            command: Comando com parâmetros

        Returns:
            Relatório de cashflow
        """
        with self.uow:
            # 1. Buscar transactions no período
            transactions = self.transaction_repository.find_by_date_range(
                from_date=command.from_date,
                to_date=command.to_date,
            )

            # 2. Buscar todas as contas (para lookup)
            all_accounts = self.account_repository.list_all()
            accounts_by_id = {acc.id: acc for acc in all_accounts}

            # 3. Agregar postings por conta
            # {account_id: {"amount": Decimal, "count": int}}
            aggregated: dict = {}

            for txn in transactions:
                for posting in txn.postings:
                    # Converter para moeda do relatório (no futuro)
                    if posting.amount.currency != command.currency:
                        continue  # Skip por enquanto (no futuro: conversão)

                    account_id = posting.account_id
                    if account_id not in aggregated:
                        aggregated[account_id] = {"amount": Decimal("0"), "count": 0}

                    aggregated[account_id]["amount"] += posting.amount.amount
                    aggregated[account_id]["count"] += 1

            # 4. Separar por tipo de conta
            income_items: list[CashflowCategoryItem] = []
            expense_items: list[CashflowCategoryItem] = []
            asset_items: list[CashflowCategoryItem] = []

            for account_id, data in aggregated.items():
                account = accounts_by_id.get(account_id)
                if not account:
                    continue

                # Aplicar filtro de prefixo se fornecido
                if command.account_code_filter:
                    if not account.code.startswith(command.account_code_filter):
                        continue

                item = CashflowCategoryItem(
                    account_code=account.code,
                    account_name=account.name,
                    amount=data["amount"],
                    transaction_count=data["count"],
                )

                if account.account_type == AccountType.INCOME:
                    income_items.append(item)
                elif account.account_type == AccountType.EXPENSE:
                    expense_items.append(item)
                elif account.account_type == AccountType.ASSET:
                    asset_items.append(item)
                # Ignora LIABILITY e EQUITY para cashflow básico

            # 5. Ordenar por amount (maior primeiro)
            income_items.sort(key=lambda x: abs(x.amount), reverse=True)
            expense_items.sort(key=lambda x: abs(x.amount), reverse=True)
            asset_items.sort(key=lambda x: abs(x.amount), reverse=True)

            # 6. Calcular totais
            # Income: valores negativos no posting (crédito) = receita positiva
            total_income = sum(abs(item.amount) for item in income_items)

            # Expense: valores positivos no posting (débito) = despesa positiva
            total_expenses = sum(abs(item.amount) for item in expense_items)

            # Net cashflow = Income - Expenses
            net_cashflow = total_income - total_expenses

            return CashflowReport(
                from_date=command.from_date,
                to_date=command.to_date,
                currency=command.currency,
                income_categories=income_items,
                total_income=total_income,
                expense_categories=expense_items,
                total_expenses=total_expenses,
                net_cashflow=net_cashflow,
                asset_balances=asset_items,
            )
