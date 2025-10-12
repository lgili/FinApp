"""
Repository Interfaces - Contratos para persistência do domínio.

Repositórios abstraem detalhes de persistência, permitindo que o
domínio seja independente de infraestrutura.

Padrão: Repository Pattern (Domain-Driven Design)

Exports:
    - IAccountRepository: Interface para persistência de contas
    - ITransactionRepository: Interface para persistência de transações
    - IImportBatchRepository: Interface para persistência de lotes
"""

from finlite.domain.repositories.account_repository import IAccountRepository
from finlite.domain.repositories.import_batch_repository import IImportBatchRepository
from finlite.domain.repositories.transaction_repository import ITransactionRepository

__all__ = [
    "IAccountRepository",
    "ITransactionRepository",
    "IImportBatchRepository",
]
