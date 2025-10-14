"""
Exemplo 05 - Workflow Completo
===============================

Este script executa um workflow completo de ponta a ponta:
1. Cria estrutura de contas
2. Cria algumas transações manuais
3. Importa CSV
4. Gera relatório

Execução:
    python examples/05_full_workflow.py
    
Opções:
    python examples/05_full_workflow.py --reset  # Limpa banco antes
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta
import argparse

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from finlite.domain.entities.account import Account
from finlite.domain.entities.transaction import Transaction
from finlite.domain.value_objects.account_type import AccountType
from finlite.domain.value_objects.posting import Posting
from finlite.domain.value_objects.money import Money
from finlite.application.use_cases.import_nubank_statement import (
    ImportNubankStatement,
    ImportNubankStatementCommand
)
from finlite.domain.exceptions import DuplicateImportError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from finlite.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from finlite.infrastructure.persistence.sqlalchemy import models
from finlite.infrastructure.persistence.sqlalchemy.repositories.import_batch_repository import (
    SqlAlchemyImportBatchRepository
)
from finlite.infrastructure.persistence.sqlalchemy.repositories.statement_entry_repository import (
    SqlAlchemyStatementEntryRepository
)
from finlite.shared.event_bus import InMemoryEventBus
from finlite.infrastructure.persistence.sqlalchemy import models


def reset_database():
    """Limpa o banco de dados."""
    print("🗑️  Limpando banco de dados...")
    # Cria engine local para reset
    engine = create_engine("sqlite:///backend/finlite.db", echo=False)
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    print("✅ Banco limpo!")


def step1_create_accounts(uow):
    """Passo 1: Criar estrutura de contas."""
    print("\n" + "=" * 60)
    print("📊 PASSO 1: Criar estrutura de contas")
    print("=" * 60)
    
    # Idempotent creation: reuse accounts already present
    with uow:
        def ensure(name, account_type, currency, parent_name=None):
            existing = uow.accounts.find_by_name(name)
            if existing:
                return existing

            parent_id = None
            if parent_name:
                parent = uow.accounts.find_by_name(parent_name)
                parent_id = parent.id if parent else None

            acc = Account.create(name, account_type, currency, parent_id)
            uow.accounts.add(acc)
            return acc

        # Assets
        assets = ensure("Assets", AccountType.ASSET, "BRL")
        bank = ensure("Assets:Bank", AccountType.ASSET, "BRL", parent_name="Assets")
        nubank = ensure("Assets:Bank:Nubank", AccountType.ASSET, "BRL", parent_name="Assets:Bank")
        cash = ensure("Assets:Cash", AccountType.ASSET, "BRL", parent_name="Assets")

        # Expenses
        expenses = ensure("Expenses", AccountType.EXPENSE, "BRL")
        food = ensure("Expenses:Food", AccountType.EXPENSE, "BRL", parent_name="Expenses")
        transport = ensure("Expenses:Transport", AccountType.EXPENSE, "BRL", parent_name="Expenses")
        entertainment = ensure("Expenses:Entertainment", AccountType.EXPENSE, "BRL", parent_name="Expenses")

        # Income
        income = ensure("Income", AccountType.INCOME, "BRL")
        salary = ensure("Income:Salary", AccountType.INCOME, "BRL", parent_name="Income")

        uow.commit()
    
    print("✅ Contas criadas:")
    print("  • Assets (Bank, Cash)")
    print("  • Expenses (Food, Transport, Entertainment)")
    print("  • Income (Salary)")
    
    return {
        'nubank': nubank,
        'cash': cash,
        'food': food,
        'transport': transport,
        'entertainment': entertainment,
        'salary': salary
    }


def step2_create_transactions(uow, accounts):
    """Passo 2: Criar transações manuais."""
    print("\n" + "=" * 60)
    print("💸 PASSO 2: Criar transações manuais")
    print("=" * 60)
    
    with uow:
        # Salário
        salary_txn = Transaction.create(
            description="Salário Outubro 2025",
            date=date.today() - timedelta(days=10),
            postings=[
                Posting(accounts['nubank'].id, Money(Decimal("5000.00"), "BRL")),
                Posting(accounts['salary'].id, Money(Decimal("-5000.00"), "BRL")),
            ],
            tags=["salary", "income"],
        )
        uow.transactions.add(salary_txn)
        
        # Supermercado
        grocery_txn = Transaction.create(
            description="Supermercado",
            date=date.today() - timedelta(days=5),
            postings=[
                Posting(accounts['nubank'].id, Money(Decimal("-200.00"), "BRL")),
                Posting(accounts['food'].id, Money(Decimal("200.00"), "BRL")),
            ],
            tags=["groceries", "food"],
        )
        uow.transactions.add(grocery_txn)
        
        # Cinema
        cinema_txn = Transaction.create(
            description="Cinema",
            date=date.today() - timedelta(days=3),
            postings=[
                Posting(accounts['cash'].id, Money(Decimal("-50.00"), "BRL")),
                Posting(accounts['entertainment'].id, Money(Decimal("50.00"), "BRL")),
            ],
            tags=["entertainment", "social"],
        )
        uow.transactions.add(cinema_txn)
        
        uow.commit()
    
    print("✅ Transações criadas:")
    print("  • Salário: R$ 5.000,00")
    print("  • Supermercado: R$ 200,00")
    print("  • Cinema: R$ 50,00")


def step3_import_csv(session):
    """Passo 3: Importar CSV."""
    print("\n" + "=" * 60)
    print("📥 PASSO 3: Importar extrato CSV")
    print("=" * 60)
    
    csv_file = Path(__file__).parent / "data" / "nubank_example.csv"
    
    if not csv_file.exists():
        print("⚠️  Arquivo CSV não encontrado, pulando importação")
        return None
    
    batch_repo = SqlAlchemyImportBatchRepository(session)
    entry_repo = SqlAlchemyStatementEntryRepository(session)
    event_bus = InMemoryEventBus()
    
    use_case = ImportNubankStatement(
        import_batch_repository=batch_repo,
        statement_entry_repository=entry_repo,
        event_bus=event_bus,
    )
    
    command = ImportNubankStatementCommand(
        file_path=csv_file,
        default_currency="BRL",
        account_hint="Assets:Bank:Nubank"
    )
    
    try:
        result = use_case.execute(command)
        print(f"✅ CSV importado:")
        print(f"  • Batch ID: {result.batch_id}")
        print(f"  • Entries: {result.entries_count}")
        return result
    except DuplicateImportError:
        print("⚠️  CSV já foi importado anteriormente")
        return None


def step4_generate_report(uow):
    """Passo 4: Gerar relatório."""
    print("\n" + "=" * 60)
    print("📊 PASSO 4: Relatório Financeiro")
    print("=" * 60)
    
    with uow:
        # Buscar dados
        all_accounts = uow.accounts.list_all()
        all_transactions = uow.transactions.list_all()
        
        # Calcular saldo
        def calculate_balance(account_id):
            balance = Decimal("0")
            for txn in all_transactions:
                for posting in txn.postings:
                    if posting.account_id == account_id:
                        balance += posting.amount
            return balance
        
        # Assets
        print("\n💰 ATIVOS (Assets):")
        asset_accounts = [a for a in all_accounts if a.account_type == AccountType.ASSET]
        total_assets = Decimal("0")
        
        for acc in asset_accounts:
            balance = calculate_balance(acc.id)
            if balance != 0 or "Bank" in acc.name or "Cash" in acc.name:
                indent = "  " * (acc.name.count(":") + 1)
                print(f"{indent}{acc.name}: R$ {balance:.2f}")
                total_assets += balance
        
        print(f"\n  TOTAL ATIVOS: R$ {total_assets:.2f}")
        
        # Expenses
        print("\n💸 DESPESAS (Expenses):")
        expense_accounts = [a for a in all_accounts if a.account_type == AccountType.EXPENSE]
        total_expenses = Decimal("0")
        
        expenses_by_category = {}
        for acc in expense_accounts:
            balance = calculate_balance(acc.id)
            if balance > 0:
                expenses_by_category[acc.name] = balance
                total_expenses += balance
        
        # Top 5 categorias
        sorted_expenses = sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)
        for acc_name, amount in sorted_expenses[:5]:
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            print(f"  {acc_name}: R$ {amount:.2f} ({percentage:.1f}%)")
        
        print(f"\n  TOTAL DESPESAS: R$ {total_expenses:.2f}")
        
        # Income
        print("\n💵 RECEITAS (Income):")
        income_accounts = [a for a in all_accounts if a.account_type == AccountType.INCOME]
        total_income = Decimal("0")
        
        for acc in income_accounts:
            balance = abs(calculate_balance(acc.id))
            if balance > 0:
                print(f"  {acc.name}: R$ {balance:.2f}")
                total_income += balance
        
        print(f"\n  TOTAL RECEITAS: R$ {total_income:.2f}")
        
        # Resumo
        print("\n" + "=" * 60)
        print("📈 RESUMO:")
        print(f"  • Receitas: R$ {total_income:.2f}")
        print(f"  • Despesas: R$ {total_expenses:.2f}")
        print(f"  • Saldo: R$ {total_income - total_expenses:.2f}")
        print(f"  • Transações: {len(all_transactions)}")
        print("=" * 60)


def main():
    """Executa workflow completo."""
    parser = argparse.ArgumentParser(description="FinApp - Workflow Completo")
    parser.add_argument("--reset", action="store_true", help="Limpar banco antes de executar")
    args = parser.parse_args()
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║              FinApp - Workflow Completo                       ║
    ║                                                               ║
    ║  Este exemplo executa um workflow completo de ponta a ponta:  ║
    ║  1. Cria contas                                               ║
    ║  2. Cria transações manuais                                   ║
    ║  3. Importa CSV                                               ║
    ║  4. Gera relatório                                            ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Reset se solicitado
    if args.reset:
        reset_database()
        print()
    
    engine = create_engine("sqlite:///backend/finlite.db", echo=False)
    models.Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    uow = SqlAlchemyUnitOfWork(session_factory)
    
    try:
        # Executar passos
        accounts = step1_create_accounts(uow)
        step2_create_transactions(uow, accounts)
        # Criar sessão curta para repositórios do passo 3
        repo_session = session_factory()
        try:
            step3_import_csv(repo_session)
        finally:
            repo_session.close()
        step4_generate_report(uow)
        
        print("\n🎉 Workflow completo executado com sucesso!")
        print("\n💡 Experimente:")
        print("  • Criar mais transações")
        print("  • Importar outros CSVs")
        print("  • Explorar os dados com 04_query_data.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante workflow: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # UnitOfWork handles session lifecycle
        pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
