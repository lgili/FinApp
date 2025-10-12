"""Data Transfer Objects for Application Layer.

DTOs são objetos simples usados para transferir dados entre camadas.
Eles isolam a camada de aplicação dos detalhes das entidades de domínio.
"""

from .account_dto import AccountDTO, CreateAccountDTO
from .transaction_dto import (
    TransactionDTO,
    PostingDTO,
    CreateTransactionDTO,
    CreatePostingDTO,
    TransactionFilterDTO,
)

__all__ = [
    # Account DTOs
    "AccountDTO",
    "CreateAccountDTO",
    # Transaction DTOs
    "TransactionDTO",
    "PostingDTO",
    "CreateTransactionDTO",
    "CreatePostingDTO",
    "TransactionFilterDTO",
]
