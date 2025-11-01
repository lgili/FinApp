"""
Post Pending Entries Use Case - Converte statement entries em transações contábeis.

Responsabilidade: Criar transações balanceadas a partir de entries com status IMPORTED.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Iterable
from uuid import UUID, uuid4

from finlite.domain.value_objects.posting import Posting
from finlite.domain.entities.statement_entry import StatementEntry, StatementStatus
from finlite.domain.entities.transaction import Transaction
from finlite.domain.repositories.account_repository import IAccountRepository
from finlite.domain.repositories.statement_entry_repository import IStatementEntryRepository
from finlite.domain.repositories.transaction_repository import ITransactionRepository
from finlite.domain.value_objects.money import Money
from finlite.infrastructure.persistence.unit_of_work import UnitOfWork


@dataclass
class PostPendingEntriesCommand:
    """Command para postar entries pendentes."""

    batch_id: Optional[UUID] = None  # Se None, posta todos entries IMPORTED
    auto_post: bool = True  # Se True, posta automaticamente entries com suggested_account
    source_account_code: str = "Assets:Bank:Checking"  # Conta de origem padrão
    dry_run: bool = False  # Se True, apenas simula sem salvar
    entry_ids: Optional[tuple[UUID, ...]] = None  # Se fornecido, limita aos IDs informados


@dataclass
class PostedEntryResult:
    """Resultado de um entry postado."""

    entry_id: UUID
    external_id: str
    transaction_id: UUID
    description: str
    amount: Decimal
    currency: str
    source_account: str
    target_account: str


@dataclass
class PostPendingEntriesResult:
    """Resultado geral do posting."""

    total_entries: int
    posted_count: int
    skipped_count: int
    error_count: int
    posted_entries: list[PostedEntryResult]
    errors: list[tuple[UUID, str]]  # (entry_id, error_message)


class PostPendingEntriesUseCase:
    """
    Use case para converter statement entries em transações contábeis.

    Fluxo:
    1. Busca entries com status IMPORTED
    2. Para cada entry com suggested_account_id:
       - Cria Transaction balanceada (2 postings)
       - Posting 1: source account (bank) com valor do entry
       - Posting 2: target account (expense/income) com valor invertido
    3. Marca entry como POSTED
    4. Salva transaction e atualiza entry

    Examples:
        >>> # Postar entries de um batch
        >>> result = use_case.execute(
        ...     PostPendingEntriesCommand(
        ...         batch_id=batch_id,
        ...         source_account_code="Assets:Bank:Nubank",
        ...         auto_post=True
        ...     )
        ... )
        >>> print(f"Posted: {result.posted_count}/{result.total_entries}")
    """

    def __init__(
        self,
        uow: UnitOfWork,
        account_repository: IAccountRepository,
        statement_repository: IStatementEntryRepository,
        transaction_repository: ITransactionRepository,
    ):
        """
        Initialize use case.

        Args:
            uow: Unit of Work para gerenciar transação
            account_repository: Repository de contas
            statement_repository: Repository de statement entries
            transaction_repository: Repository de transactions
        """
        self.uow = uow
        self.account_repository = account_repository
        self.statement_repository = statement_repository
        self.transaction_repository = transaction_repository

    def execute(self, command: PostPendingEntriesCommand) -> PostPendingEntriesResult:
        """
        Executa posting de entries pendentes.

        Args:
            command: Comando com parâmetros

        Returns:
            Resultado com estatísticas e entries postados

        Raises:
            ValueError: Se source_account não existir
        """
        with self.uow:
            # 1. Buscar source account
            source_account = self.account_repository.find_by_code(command.source_account_code)
            if not source_account:
                raise ValueError(f"Source account not found: {command.source_account_code}")

            statement_repo = getattr(self.uow, "statement_repository", self.statement_repository)

            # 2. Buscar entries IMPORTED
            ids_filter = set(command.entry_ids) if command.entry_ids else None

            if command.batch_id:
                all_entries = statement_repo.find_by_batch_id(command.batch_id)
                entries = [e for e in all_entries if e.is_imported()]
            else:
                entries = statement_repo.find_by_status(StatementStatus.IMPORTED)

            if ids_filter is not None:
                entries = [entry for entry in entries if entry.id in ids_filter]

            if not entries:
                return PostPendingEntriesResult(
                    total_entries=0,
                    posted_count=0,
                    skipped_count=0,
                    error_count=0,
                    posted_entries=[],
                    errors=[],
                )

            # 3. Processar cada entry
            posted_entries: list[PostedEntryResult] = []
            errors: list[tuple[UUID, str]] = []
            skipped_count = 0

            for entry in entries:
                try:
                    # Skip se não tiver suggested_account e auto_post
                    if command.auto_post and not entry.suggested_account_id:
                        skipped_count += 1
                        continue

                    # Buscar target account
                    if entry.suggested_account_id:
                        target_account = self.account_repository.get(entry.suggested_account_id)
                    else:
                        # Se não tem sugestão e não é auto_post, precisa de conta manual
                        # Por ora, skip (no futuro pode ter uma conta "Uncategorized")
                        skipped_count += 1
                        continue

                    # 4. Criar Transaction balanceada
                    transaction = self._create_transaction_from_entry(
                        entry=entry,
                        source_account_id=source_account.id,
                        target_account_id=target_account.id,
                    )

                    # 5. Salvar transaction (se não for dry-run)
                    if not command.dry_run:
                        self.transaction_repository.add(transaction)

                        # 6. Marcar entry como POSTED
                        entry.mark_posted(transaction.id)
                        statement_repo.update(entry)

                    # 7. Adicionar ao resultado
                    posted_entries.append(
                        PostedEntryResult(
                            entry_id=entry.id,
                            external_id=entry.external_id,
                            transaction_id=transaction.id,
                            description=entry.memo,
                            amount=entry.amount,
                            currency=entry.currency,
                            source_account=source_account.code,
                            target_account=target_account.code,
                        )
                    )

                except Exception as e:
                    errors.append((entry.id, str(e)))

            # 8. Commit se não for dry-run
            if not command.dry_run:
                self.uow.commit()

            return PostPendingEntriesResult(
                total_entries=len(entries),
                posted_count=len(posted_entries),
                skipped_count=skipped_count,
                error_count=len(errors),
                posted_entries=posted_entries,
                errors=errors,
            )

    def _create_transaction_from_entry(
        self,
        entry: StatementEntry,
        source_account_id: UUID,
        target_account_id: UUID,
    ) -> Transaction:
        """
        Cria Transaction balanceada a partir de StatementEntry.

        Lógica:
        - Entry com amount negativo (débito): saída da conta source
          -> Posting 1: source account com amount negativo
          -> Posting 2: target account (expense) com amount positivo

        - Entry com amount positivo (crédito): entrada na conta source
          -> Posting 1: source account com amount positivo
          -> Posting 2: target account (income) com amount negativo

        Args:
            entry: Statement entry
            source_account_id: ID da conta de origem (bank)
            target_account_id: ID da conta de destino (expense/income)

        Returns:
            Transaction balanceada
        """
        # Criar postings
        money_entry = Money(amount=entry.amount, currency=entry.currency)

        # Posting 1: Source account (bank) com amount do entry
        posting_source = Posting(
            account_id=source_account_id,
            amount=money_entry,
        )

        # Posting 2: Target account com amount invertido (para balancear)
        money_target = Money(amount=-entry.amount, currency=entry.currency)
        posting_target = Posting(
            account_id=target_account_id,
            amount=money_target,
        )

        # Criar transaction
        transaction = Transaction.create(
            date=entry.occurred_at.date(),
            description=entry.memo,
            postings=[posting_source, posting_target],
            tags=[f"import:{entry.batch_id}"],
        )

        return transaction
