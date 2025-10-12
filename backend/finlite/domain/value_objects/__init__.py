"""
Value Objects - Objetos imutáveis que representam conceitos do domínio.

Value objects não têm identidade própria - são comparados por valor.
São imutáveis para garantir consistência e thread-safety.

Exports:
    - Money: Valor monetário com moeda (ex: BRL 100.50)
    - AccountType: Enum de tipos de conta (ASSET, LIABILITY, etc)
    - Posting: Lançamento contábil individual (account + amount)
    - validate_postings_balance: Função para validar balanceamento
"""

from finlite.domain.value_objects.account_type import AccountType
from finlite.domain.value_objects.money import Money
from finlite.domain.value_objects.posting import Posting, validate_postings_balance

__all__ = [
    "Money",
    "AccountType",
    "Posting",
    "validate_postings_balance",
]
