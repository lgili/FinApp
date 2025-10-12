"""
Domain Layer - Lógica de negócio pura.

Esta camada contém o coração do sistema: regras de negócio,
entidades, value objects e interfaces de repositórios.

NÃO deve depender de nenhuma camada externa (DB, UI, frameworks).

Estrutura:
- entities/: Objetos com identidade (Account, Transaction)
- value_objects/: Objetos imutáveis comparados por valor (Money, Posting)
- repositories/: Interfaces para persistência (IAccountRepository)
- exceptions.py: Exceções específicas de domínio
"""

# Value Objects
from finlite.domain.value_objects import (
    AccountType,
    Money,
    Posting,
    validate_postings_balance,
)

# Entities
from finlite.domain.entities import (
    Account,
    ImportBatch,
    ImportSource,
    ImportStatus,
    Transaction,
)

# Repository Interfaces
from finlite.domain.repositories import (
    IAccountRepository,
    IImportBatchRepository,
    ITransactionRepository,
)

# Exceptions
from finlite.domain import exceptions

__all__ = [
    # Value Objects
    "Money",
    "AccountType",
    "Posting",
    "validate_postings_balance",
    # Entities
    "Account",
    "Transaction",
    "ImportBatch",
    "ImportSource",
    "ImportStatus",
    # Repository Interfaces
    "IAccountRepository",
    "ITransactionRepository",
    "IImportBatchRepository",
    # Exceptions module
    "exceptions",
]

