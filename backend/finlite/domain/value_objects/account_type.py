"""
AccountType Enum - Tipos de contas contábeis.

Implementa os 5 tipos fundamentais da contabilidade de partida dobrada:
- ASSET (Ativo): Recursos que a pessoa possui (banco, investimentos)
- LIABILITY (Passivo): Dívidas e obrigações (cartão de crédito, empréstimos)
- EQUITY (Patrimônio Líquido): Capital inicial, lucros acumulados
- INCOME (Receita): Entradas de dinheiro (salário, vendas)
- EXPENSE (Despesa): Saídas de dinheiro (aluguel, alimentação)

Referência: Equação Contábil Fundamental
    Ativo = Passivo + Patrimônio Líquido
    Lucro = Receita - Despesa
"""

from enum import Enum


class AccountType(str, Enum):
    """
    Enum para tipos de contas contábeis.

    Herda de str para facilitar serialização/deserialização.

    Attributes:
        ASSET: Contas de ativo (ex: "Assets:Checking", "Assets:Investments")
        LIABILITY: Contas de passivo (ex: "Liabilities:CreditCard", "Liabilities:Loan")
        EQUITY: Patrimônio líquido (ex: "Equity:OpeningBalances")
        INCOME: Contas de receita (ex: "Income:Salary", "Income:Bonus")
        EXPENSE: Contas de despesa (ex: "Expenses:Rent", "Expenses:Food")

    Examples:
        >>> AccountType.ASSET
        <AccountType.ASSET: 'ASSET'>

        >>> AccountType.ASSET.value
        'ASSET'

        >>> AccountType("EXPENSE")
        <AccountType.EXPENSE: 'EXPENSE'>

        >>> AccountType.INCOME.is_debit_positive()
        False

        >>> AccountType.EXPENSE.is_debit_positive()
        True
    """

    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

    def is_debit_positive(self) -> bool:
        """
        Determina se débito aumenta o saldo (natureza devedora).

        Em contabilidade de partida dobrada:
        - ASSET e EXPENSE: Débito aumenta (+), Crédito diminui (-)
        - LIABILITY, EQUITY, INCOME: Crédito aumenta (+), Débito diminui (-)

        Returns:
            True se débito aumenta saldo (ASSET, EXPENSE)
            False se crédito aumenta saldo (LIABILITY, EQUITY, INCOME)

        Examples:
            >>> AccountType.ASSET.is_debit_positive()
            True  # Débito em conta de banco aumenta saldo

            >>> AccountType.INCOME.is_debit_positive()
            False  # Crédito em conta de receita aumenta saldo
        """
        return self in (AccountType.ASSET, AccountType.EXPENSE)

    def is_credit_positive(self) -> bool:
        """
        Determina se crédito aumenta o saldo (natureza credora).

        Returns:
            True se crédito aumenta saldo (LIABILITY, EQUITY, INCOME)
            False se débito aumenta saldo (ASSET, EXPENSE)

        Examples:
            >>> AccountType.LIABILITY.is_credit_positive()
            True  # Crédito em conta de cartão aumenta dívida

            >>> AccountType.EXPENSE.is_credit_positive()
            False  # Débito em despesa aumenta gasto
        """
        return not self.is_debit_positive()

    def is_balance_sheet_account(self) -> bool:
        """
        Verifica se é conta de balanço patrimonial.

        Contas de balanço: ASSET, LIABILITY, EQUITY
        (representam posição financeira em um momento específico)

        Returns:
            True se for conta de balanço

        Examples:
            >>> AccountType.ASSET.is_balance_sheet_account()
            True

            >>> AccountType.INCOME.is_balance_sheet_account()
            False
        """
        return self in (AccountType.ASSET, AccountType.LIABILITY, AccountType.EQUITY)

    def is_income_statement_account(self) -> bool:
        """
        Verifica se é conta de demonstração de resultado.

        Contas de resultado: INCOME, EXPENSE
        (representam fluxo de dinheiro em um período)

        Returns:
            True se for conta de resultado

        Examples:
            >>> AccountType.EXPENSE.is_income_statement_account()
            True

            >>> AccountType.EQUITY.is_income_statement_account()
            False
        """
        return self in (AccountType.INCOME, AccountType.EXPENSE)

    def get_sign_multiplier(self) -> int:
        """
        Retorna multiplicador de sinal para cálculos.

        Útil para converter débito/crédito em valores positivos/negativos
        ao calcular saldos.

        Returns:
            +1 para contas de natureza devedora (ASSET, EXPENSE)
            -1 para contas de natureza credora (LIABILITY, EQUITY, INCOME)

        Examples:
            >>> AccountType.ASSET.get_sign_multiplier()
            1

            >>> AccountType.INCOME.get_sign_multiplier()
            -1

            # Uso em cálculo de saldo:
            >>> account_type = AccountType.ASSET
            >>> debit = 1000
            >>> credit = 500
            >>> balance = (debit - credit) * account_type.get_sign_multiplier()
            >>> balance
            500  # Saldo positivo para ASSET
        """
        return 1 if self.is_debit_positive() else -1

    @classmethod
    def from_string(cls, value: str) -> "AccountType":
        """
        Cria AccountType a partir de string (case-insensitive).

        Args:
            value: String com tipo de conta

        Returns:
            Enum correspondente

        Raises:
            ValueError: Se valor for inválido

        Examples:
            >>> AccountType.from_string("asset")
            <AccountType.ASSET: 'ASSET'>

            >>> AccountType.from_string("EXPENSE")
            <AccountType.EXPENSE: 'EXPENSE'>

            >>> AccountType.from_string("invalid")
            ValueError: Invalid account type: 'invalid'
        """
        try:
            return cls(value.upper())
        except ValueError:
            valid_types = ", ".join([t.value for t in cls])
            raise ValueError(
                f"Invalid account type: '{value}'. "
                f"Must be one of: {valid_types}"
            )

    def __str__(self) -> str:
        """Representação string legível."""
        return self.value

    def __repr__(self) -> str:
        """Representação técnica para debug."""
        return f"<AccountType.{self.name}: '{self.value}'>"
