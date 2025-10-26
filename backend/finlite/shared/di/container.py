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
    ImportBatchMapper,
    StatementEntryMapper,
    TransactionMapper,
)
from finlite.infrastructure.persistence.sqlalchemy.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyCardStatementRepository,
    SqlAlchemyImportBatchRepository,
    SqlAlchemyStatementEntryRepository,
    SqlAlchemyTransactionRepository,
)
from finlite.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from finlite.infrastructure.events import InMemoryEventBus, AuditLogHandler
from finlite.application.use_cases import (
    CreateAccountUseCase,
    RecordTransactionUseCase,
    ListAccountsUseCase,
    GetAccountBalanceUseCase,
    ListTransactionsUseCase,
)
from finlite.application.use_cases.import_nubank_statement import (
    ImportNubankStatement,
)
from finlite.application.use_cases.apply_rules import ApplyRulesUseCase
from finlite.application.use_cases.post_pending_entries import PostPendingEntriesUseCase
from finlite.application.use_cases.generate_cashflow_report import (
    GenerateCashflowReportUseCase,
)
from finlite.application.use_cases.generate_balance_sheet_report import (
    GenerateBalanceSheetReportUseCase,
)
from finlite.application.use_cases.generate_income_statement_report import (
    GenerateIncomeStatementReportUseCase,
)
from finlite.application.use_cases.generate_monthly_tax_report import (
    MonthlyTaxReportUseCase,
)
from finlite.application.use_cases.export_beancount import ExportBeancountUseCase
from finlite.application.use_cases.build_card_statement import BuildCardStatementUseCase
from finlite.application.use_cases.pay_card import PayCardUseCase
from finlite.config import Settings


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

    import_batch_mapper = providers.Singleton(ImportBatchMapper)

    statement_entry_mapper = providers.Singleton(StatementEntryMapper)

    transaction_mapper = providers.Singleton(TransactionMapper)

    # =========================================================================
    # Repositories
    # =========================================================================

    account_repository = providers.Factory(
        SqlAlchemyAccountRepository,
        session=session_factory,
    )

    import_batch_repository = providers.Factory(
        SqlAlchemyImportBatchRepository,
        session=session_factory,
    )

    statement_entry_repository = providers.Factory(
        SqlAlchemyStatementEntryRepository,
        session=session_factory,
    )

    transaction_repository = providers.Factory(
        SqlAlchemyTransactionRepository,
        session=session_factory,
    )

    card_statement_repository = providers.Factory(
        SqlAlchemyCardStatementRepository,
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
    # Event Bus & Handlers
    # =========================================================================

    event_bus = providers.Singleton(
        InMemoryEventBus,
    )

    audit_log_handler = providers.Singleton(
        AuditLogHandler,
    )

    # =========================================================================
    # Use Cases
    # =========================================================================

    create_account_use_case = providers.Factory(
        CreateAccountUseCase,
        uow=unit_of_work,
        event_bus=event_bus,
    )

    record_transaction_use_case = providers.Factory(
        RecordTransactionUseCase,
        uow=unit_of_work,
        event_bus=event_bus,
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

    import_nubank_statement_use_case = providers.Factory(
        ImportNubankStatement,
        import_batch_repository=import_batch_repository,
        statement_entry_repository=statement_entry_repository,
        event_bus=event_bus,
    )

    apply_rules_use_case = providers.Factory(
        ApplyRulesUseCase,
        uow=unit_of_work,
        account_repository=account_repository,
        statement_repository=statement_entry_repository,
        settings=providers.Singleton(Settings),
    )

    post_pending_entries_use_case = providers.Factory(
        PostPendingEntriesUseCase,
        uow=unit_of_work,
        account_repository=account_repository,
        statement_repository=statement_entry_repository,
        transaction_repository=transaction_repository,
    )

    generate_cashflow_report_use_case = providers.Factory(
        GenerateCashflowReportUseCase,
        uow=unit_of_work,
        account_repository=account_repository,
        transaction_repository=transaction_repository,
    )

    generate_balance_sheet_report_use_case = providers.Factory(
        GenerateBalanceSheetReportUseCase,
        uow=unit_of_work,
        account_repository=account_repository,
        transaction_repository=transaction_repository,
    )

    generate_income_statement_report_use_case = providers.Factory(
        GenerateIncomeStatementReportUseCase,
        uow=unit_of_work,
        account_repository=account_repository,
        transaction_repository=transaction_repository,
    )

    generate_monthly_tax_report_use_case = providers.Factory(
        MonthlyTaxReportUseCase,
        uow=unit_of_work,
    )

    export_beancount_use_case = providers.Factory(
        ExportBeancountUseCase,
        uow=unit_of_work,
        account_repository=account_repository,
        transaction_repository=transaction_repository,
    )

    build_card_statement_use_case = providers.Factory(
        BuildCardStatementUseCase,
        uow=unit_of_work,
        account_repository=account_repository,
        transaction_repository=transaction_repository,
        card_statement_repository=card_statement_repository,
    )

    pay_card_use_case = providers.Factory(
        PayCardUseCase,
        uow=unit_of_work,
        account_repository=account_repository,
        transaction_repository=transaction_repository,
        card_statement_repository=card_statement_repository,
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
    
    # Setup event bus with handlers
    _setup_event_bus(container)
    
    return container


def _setup_event_bus(container: Container) -> None:
    """
    Configure event bus with default handlers.
    
    Args:
        container: Container with event bus and handlers
    """
    from finlite.domain.events import AccountCreated, TransactionRecorded
    from finlite.domain.events.statement_events import (
        StatementImported,
        StatementImportFailed,
        StatementMatched,
        StatementPosted,
    )
    
    event_bus = container.event_bus()
    audit_handler = container.audit_log_handler()
    
    # Subscribe audit handler to all domain events
    event_bus.subscribe(AccountCreated, audit_handler.handle)
    event_bus.subscribe(TransactionRecorded, audit_handler.handle)
    
    # Subscribe to statement import events
    event_bus.subscribe(StatementImported, audit_handler.handle)
    event_bus.subscribe(StatementImportFailed, audit_handler.handle)
    event_bus.subscribe(StatementMatched, audit_handler.handle)
    event_bus.subscribe(StatementPosted, audit_handler.handle)


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
