"""
Entities - Objetos de domínio com identidade e ciclo de vida.

Entities são definidas por sua identidade (UUID), não por seus atributos.
Duas entities com mesmo ID são iguais, mesmo com atributos diferentes.

Exports:
    - Account: Conta contábil hierárquica
    - Transaction: Transação de partida dobrada (aggregate root)
    - ImportBatch: Lote de importação de transações
"""

from finlite.domain.entities.account import Account
from finlite.domain.entities.import_batch import (
    ImportBatch,
    ImportSource,
    ImportStatus,
)
from finlite.domain.entities.transaction import Transaction

__all__ = [
    "Account",
    "Transaction",
    "ImportBatch",
    "ImportSource",
    "ImportStatus",
]

