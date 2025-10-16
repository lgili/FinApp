"""
Apply Rules Use Case - Aplica regras de classificação a statement entries importados.

Responsabilidade: Sugerir contas contábeis baseado em regras de pattern matching.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from finlite.config import Settings
from finlite.domain.entities.statement_entry import StatementEntry
from finlite.domain.repositories.account_repository import IAccountRepository
from finlite.domain.repositories.statement_entry_repository import IStatementEntryRepository
from finlite.infrastructure.persistence.unit_of_work import UnitOfWork
from finlite.rules.mapping import find_matching_rule, load_rules


@dataclass
class ApplyRulesCommand:
    """Command para aplicar regras."""

    batch_id: Optional[UUID] = None  # Se None, aplica em todos entries IMPORTED
    auto_apply: bool = True  # Se True, salva sugestões automaticamente
    dry_run: bool = False  # Se True, apenas simula sem salvar


@dataclass
class RuleApplicationResult:
    """Resultado da aplicação de regras."""

    entry_id: UUID
    external_id: str
    memo: str
    suggested_account_code: Optional[str]
    rule_pattern: Optional[str]
    confidence: str  # "high" (rule match) or "none"


@dataclass
class ApplyRulesResult:
    """Resultado geral da aplicação."""

    total_entries: int
    matched_entries: int
    unmatched_entries: int
    applications: list[RuleApplicationResult]


class ApplyRulesUseCase:
    """
    Use case para aplicar regras de classificação a statement entries.

    Fluxo:
    1. Busca entries com status IMPORTED (filtrados por batch_id se fornecido)
    2. Para cada entry, tenta encontrar regra matching
    3. Se encontrar, sugere conta (suggest_account)
    4. Retorna estatísticas e detalhes

    Examples:
        >>> # Aplicar regras em batch específico
        >>> result = use_case.execute(
        ...     ApplyRulesCommand(batch_id=batch_id, auto_apply=True)
        ... )
        >>> print(f"Matched: {result.matched_entries}/{result.total_entries}")
    """

    def __init__(
        self,
        uow: UnitOfWork,
        account_repository: IAccountRepository,
        statement_repository: IStatementEntryRepository,
        settings: Settings,
    ):
        """
        Initialize use case.

        Args:
            uow: Unit of Work para gerenciar transação
            account_repository: Repository de contas
            statement_repository: Repository de statement entries
            settings: Settings da aplicação (para carregar regras)
        """
        self.uow = uow
        self.account_repository = account_repository
        self.statement_repository = statement_repository
        self.settings = settings

    def execute(self, command: ApplyRulesCommand) -> ApplyRulesResult:
        """
        Executa aplicação de regras.

        Args:
            command: Comando com parâmetros

        Returns:
            Resultado com estatísticas e aplicações

        Raises:
            ValueError: Se batch_id fornecido não existir
        """
        with self.uow:
            # 1. Carregar regras
            rules = load_rules(self.settings)
            if not rules:
                # Sem regras, retorna vazio
                return ApplyRulesResult(
                    total_entries=0,
                    matched_entries=0,
                    unmatched_entries=0,
                    applications=[],
                )

            # 2. Buscar entries IMPORTED
            if command.batch_id:
                # Filtrar por batch específico
                all_entries = self.statement_repository.find_by_batch_id(command.batch_id)
                entries = [e for e in all_entries if e.is_imported()]
            else:
                # Buscar todos entries IMPORTED
                entries = self.statement_repository.find_by_status("imported")

            if not entries:
                return ApplyRulesResult(
                    total_entries=0,
                    matched_entries=0,
                    unmatched_entries=0,
                    applications=[],
                )

            # 3. Aplicar regras em cada entry
            applications: list[RuleApplicationResult] = []
            matched_count = 0

            for entry in entries:
                # Determinar se é despesa ou receita baseado no amount
                is_expense = entry.is_debit()  # amount < 0 é despesa

                # Buscar regra matching
                match_result = find_matching_rule(
                    rules,
                    text=entry.memo,
                    is_expense=is_expense,
                    amount=entry.amount,
                    occurred_at=entry.occurred_at,
                )

                if match_result is not None:
                    _, rule = match_result

                    # Buscar conta por code
                    account = self.account_repository.find_by_code(rule.account)

                    if account:
                        # Aplicar sugestão
                        if command.auto_apply and not command.dry_run:
                            entry.suggest_account(account.id)
                            entry.add_metadata("rule_pattern", rule.pattern)
                            entry.add_metadata("rule_account", rule.account)
                            self.statement_repository.save(entry)

                        matched_count += 1
                        applications.append(
                            RuleApplicationResult(
                                entry_id=entry.id,
                                external_id=entry.external_id,
                                memo=entry.memo,
                                suggested_account_code=rule.account,
                                rule_pattern=rule.pattern,
                                confidence="high",
                            )
                        )
                    else:
                        # Regra matched mas conta não existe
                        applications.append(
                            RuleApplicationResult(
                                entry_id=entry.id,
                                external_id=entry.external_id,
                                memo=entry.memo,
                                suggested_account_code=None,
                                rule_pattern=rule.pattern,
                                confidence="none",
                            )
                        )
                else:
                    # Nenhuma regra matched
                    applications.append(
                        RuleApplicationResult(
                            entry_id=entry.id,
                            external_id=entry.external_id,
                            memo=entry.memo,
                            suggested_account_code=None,
                            rule_pattern=None,
                            confidence="none",
                        )
                    )

            # 4. Commit se não for dry-run
            if not command.dry_run:
                self.uow.commit()

            return ApplyRulesResult(
                total_entries=len(entries),
                matched_entries=matched_count,
                unmatched_entries=len(entries) - matched_count,
                applications=applications,
            )
