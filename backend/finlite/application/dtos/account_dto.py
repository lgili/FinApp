"""Account Data Transfer Objects."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class AccountDTO:
    """DTO for Account output."""

    id: UUID
    code: str
    name: str
    type: str  # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    currency: str
    balance: Decimal
    parent_code: str | None = None
    is_placeholder: bool = False
    tags: tuple[str, ...] = ()

    @property
    def full_path(self) -> str:
        """Return the full account path (e.g., 'Assets:Bank:Checking')."""
        if self.parent_code:
            return f"{self.parent_code}:{self.code}"
        return self.code


@dataclass(frozen=True)
class CreateAccountDTO:
    """DTO for Account creation."""

    code: str
    name: str
    type: str  # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    currency: str
    parent_code: str | None = None
    is_placeholder: bool = False
    tags: tuple[str, ...] = ()
