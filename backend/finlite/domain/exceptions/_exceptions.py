"""
Domain Exceptions - Exceções específicas do domínio.

Exceções de domínio comunicam violações de regras de negócio
de forma explícita e type-safe.

Hierarchy:
    DomainException (base)
    ├── AccountException
    │   ├── DuplicateAccountError
    │   ├── InvalidAccountTypeError
    │   └── AccountNotFoundError
    ├── TransactionException
    │   ├── UnbalancedTransactionError
    │   ├── InvalidPostingError
    │   └── TransactionNotFoundError
    └── ImportException
        ├── DuplicateImportError
        └── ImportBatchNotFoundError

Referência: Domain-Driven Design - Ubiquitous Language
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

if TYPE_CHECKING:
    from finlite.domain.value_objects.money import Money


# =============================================================================
# Base Exception
# =============================================================================


class DomainException(Exception):
    """
    Exceção base para todas as exceções de domínio.

    Todas as exceções de domínio devem herdar desta classe.
    """

    pass


# =============================================================================
# Account Exceptions
# =============================================================================


class AccountException(DomainException):
    """Exceção base para erros relacionados a contas."""

    pass


class DuplicateAccountError(AccountException):
    """
    Erro ao tentar criar conta com nome duplicado.

    Attributes:
        account_name: Nome da conta que já existe

    Examples:
        >>> raise DuplicateAccountError("Assets:Checking")
        DuplicateAccountError: Account 'Assets:Checking' already exists
    """

    def __init__(self, account_name: str):
        self.account_name = account_name
        super().__init__(f"Account '{account_name}' already exists")


class InvalidAccountTypeError(AccountException):
    """
    Erro ao usar tipo de conta inválido.

    Attributes:
        account_type: Tipo inválido fornecido

    Examples:
        >>> raise InvalidAccountTypeError("INVALID")
        InvalidAccountTypeError: Invalid account type: 'INVALID'. Must be one of: ASSET, LIABILITY, EQUITY, INCOME, EXPENSE
    """

    def __init__(self, account_type: str):
        self.account_type = account_type
        valid_types = "ASSET, LIABILITY, EQUITY, INCOME, EXPENSE"
        super().__init__(
            f"Invalid account type: '{account_type}'. Must be one of: {valid_types}"
        )


class AccountNotFoundError(AccountException):
    """
    Erro ao buscar conta inexistente.

    Attributes:
        account_id: UUID da conta não encontrada (ou None)
        account_name: Nome da conta não encontrada (ou None)

    Examples:
        >>> from uuid import uuid4
        >>> raise AccountNotFoundError(account_id=uuid4())
        AccountNotFoundError: Account with id=... not found

        >>> raise AccountNotFoundError(account_name="Assets:NotExists")
        AccountNotFoundError: Account 'Assets:NotExists' not found
    """

    def __init__(
        self,
        account_id: Optional[UUID] = None,
        account_name: Optional[str] = None,
    ):
        self.account_id = account_id
        self.account_name = account_name

        if account_id:
            msg = f"Account with id={account_id} not found"
        elif account_name:
            msg = f"Account '{account_name}' not found"
        else:
            msg = "Account not found"

        super().__init__(msg)


# =============================================================================
# Transaction Exceptions
# =============================================================================


class TransactionException(DomainException):
    """Exceção base para erros relacionados a transações."""

    pass


class UnbalancedTransactionError(TransactionException):
    """
    Erro ao criar transação com postings desbalanceados.

    Em contabilidade de partida dobrada, toda transação deve
    ter postings que somem zero (débitos = créditos).

    Attributes:
        total: Valor do desbalanceamento
        description: Descrição da transação

    Examples:
        >>> from finlite.domain.value_objects.money import Money
        >>> total = Money.from_float(50.0, "BRL")
        >>> raise UnbalancedTransactionError(total, "Compra no mercado")
        UnbalancedTransactionError: Transaction 'Compra no mercado' is unbalanced: total is BRL 50.00 (expected 0)
    """

    def __init__(self, total: Money, description: str):
        self.total = total
        self.description = description
        super().__init__(
            f"Transaction '{description}' is unbalanced: "
            f"total is {total} (expected 0)"
        )


class InvalidPostingError(TransactionException):
    """
    Erro ao criar posting inválido.

    Attributes:
        message: Descrição do erro

    Examples:
        >>> raise InvalidPostingError("Posting amount cannot be zero")
        InvalidPostingError: Posting amount cannot be zero
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class TransactionNotFoundError(TransactionException):
    """
    Erro ao buscar transação inexistente.

    Attributes:
        transaction_id: UUID da transação não encontrada

    Examples:
        >>> from uuid import uuid4
        >>> raise TransactionNotFoundError(uuid4())
        TransactionNotFoundError: Transaction with id=... not found
    """

    def __init__(self, transaction_id: UUID):
        self.transaction_id = transaction_id
        super().__init__(f"Transaction with id={transaction_id} not found")


# =============================================================================
# Import Exceptions
# =============================================================================


class ImportException(DomainException):
    """Exceção base para erros relacionados a importação."""

    pass


class DuplicateImportError(ImportException):
    """
    Erro ao tentar importar arquivo/lote duplicado.

    Attributes:
        source: Identificador da fonte (ex: arquivo)
        batch_id: UUID do lote duplicado (opcional)

    Examples:
        >>> raise DuplicateImportError("nubank_2025-10.csv")
        DuplicateImportError: Import from 'nubank_2025-10.csv' already exists
    """

    def __init__(self, source: str, batch_id: Optional[UUID] = None):
        self.source = source
        self.batch_id = batch_id

        if batch_id:
            msg = f"Import from '{source}' already exists (batch_id={batch_id})"
        else:
            msg = f"Import from '{source}' already exists"

        super().__init__(msg)


class ImportBatchNotFoundError(ImportException):
    """
    Erro ao buscar lote de importação inexistente.

    Attributes:
        batch_id: UUID do lote não encontrado

    Examples:
        >>> from uuid import uuid4
        >>> raise ImportBatchNotFoundError(uuid4())
        ImportBatchNotFoundError: Import batch with id=... not found
    """

    def __init__(self, batch_id: UUID):
        self.batch_id = batch_id
        super().__init__(f"Import batch with id={batch_id} not found")


# =============================================================================
# Validation Exceptions
# =============================================================================


class ValidationError(DomainException):
    """
    Erro genérico de validação de domínio.

    Use exceções mais específicas quando possível.

    Attributes:
        message: Descrição do erro
        field: Nome do campo inválido (opcional)

    Examples:
        >>> raise ValidationError("Invalid email format", field="email")
        ValidationError: Invalid email format (field: email)
    """

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field

        if field:
            super().__init__(f"{message} (field: {field})")
        else:
            super().__init__(message)
