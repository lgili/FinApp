"""Dependency Injection Container.

Este módulo configura o container de injeção de dependências usando
dependency-injector para gerenciar todas as dependências do projeto.

O container é responsável por:
- Criar instâncias de repositories
- Configurar sessões de banco de dados
- Wire use cases com suas dependências
- Gerenciar ciclo de vida dos objetos

Exemplo de uso:
    >>> from finlite.shared.di.container import Container
    >>> container = Container()
    >>> container.config.database.url.from_env("DATABASE_URL")
    >>> 
    >>> # Obter use case com dependências injetadas
    >>> create_account = container.use_cases.create_account()
    >>> result = create_account.execute(dto)
"""

from dependency_injector import containers, providers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from finlite.infrastructure.persistence.sqlalchemy.models import Base
from finlite.infrastructure.persistence.sqlalchemy.mappers import (
    AccountMapper,
    TransactionMapper,
)
from finlite.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyTransactionRepository,
)
from finlite.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from finlite.application.use_cases import (
    CreateAccountUseCase,
    RecordTransactionUseCase,
    ListAccountsUseCase,
    GetAccountBalanceUseCase,
    ListTransactionsUseCase,
)


class Container(containers.DeclarativeContainer):
    """
    Container principal de injeção de dependências.

    Organiza todas as dependências em providers hierárquicos:
    - config: Configurações (database URL, etc)
    - database: Engine, SessionFactory
    - mappers: Domain ↔ ORM mappers
    - repositories: Repository implementations
    - use_cases: Application use cases
    """

    # =========================================================================
    # Configuration
    # =========================================================================

    config = providers.Configuration()

    # =========================================================================
    # Database Infrastructure
    # =========================================================================

    database_engine = providers.Singleton(
        lambda url, echo: (
            create_engine(
                url,
                echo=echo,
                connect_args={"check_same_thread": False}
            )
            if url.startswith("sqlite")
            else create_engine(
                url,
                echo=echo,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
        ),
        url=config.database.url,
        echo=config.database.echo,
    )

    session_factory = providers.Singleton(
        lambda engine: scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine,
            )
        ),
        engine=database_engine,
    )

    # =========================================================================
    # Mappers
    # =========================================================================

    account_mapper = providers.Singleton(AccountMapper)

    transaction_mapper = providers.Singleton(TransactionMapper)

    # =========================================================================
    # Repositories
    # =========================================================================

    account_repository = providers.Factory(
        SqlAlchemyAccountRepository,
        session=session_factory,
    )

    transaction_repository = providers.Factory(
        SqlAlchemyTransactionRepository,
        session=session_factory,
    )

    # =========================================================================
    # Unit of Work
    # =========================================================================

    unit_of_work = providers.Factory(
        SqlAlchemyUnitOfWork,
        session_factory=session_factory,
    )

    # =========================================================================
    # Use Cases
    # =========================================================================

    create_account_use_case = providers.Factory(
        CreateAccountUseCase,
        uow=unit_of_work,
    )

    record_transaction_use_case = providers.Factory(
        RecordTransactionUseCase,
        uow=unit_of_work,
    )

    list_accounts_use_case = providers.Factory(
        ListAccountsUseCase,
        uow=unit_of_work,
    )

    get_account_balance_use_case = providers.Factory(
        GetAccountBalanceUseCase,
        uow=unit_of_work,
    )

    list_transactions_use_case = providers.Factory(
        ListTransactionsUseCase,
        uow=unit_of_work,
    )


def create_container(database_url: str = "sqlite:///finlite.db", echo: bool = False) -> Container:
    """
    Factory function para criar container configurado.

    Args:
        database_url: URL de conexão do banco (default: SQLite local)
        echo: Se deve logar queries SQL (default: False)

    Returns:
        Container configurado e pronto para uso

    Examples:
        >>> # SQLite em memória para testes
        >>> container = create_container("sqlite:///:memory:")
        >>> 
        >>> # PostgreSQL para produção
        >>> container = create_container("postgresql://user:pass@localhost/finlite")
        >>> 
        >>> # Usar use case
        >>> use_case = container.create_account_use_case()
        >>> result = use_case.execute(dto)
    """
    container = Container()
    container.config.database.url.from_value(database_url)
    container.config.database.echo.from_value(echo)
    return container


def init_database(container: Container) -> None:
    """
    Inicializa o banco de dados criando todas as tabelas.

    Args:
        container: Container configurado

    Examples:
        >>> container = create_container()
        >>> init_database(container)
    """
    engine = container.database_engine()
    Base.metadata.create_all(bind=engine)
