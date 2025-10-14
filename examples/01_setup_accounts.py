"""
Exemplo 01 - Setup de Contas
============================

Este script cria uma estrutura hierárquica de contas realista para uso no FinApp.

Execução:
    python examples/01_setup_accounts.py
"""

import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from finlite.domain.entities.account import Account
from finlite.domain.value_objects.account_type import AccountType
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from finlite.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from finlite.infrastructure.persistence.sqlalchemy import models


def setup_accounts():
    """Cria estrutura completa de contas."""
    
    # Use a local SQLite file database for examples. This will create
    # `backend/finlite.db` if it doesn't exist and create missing tables.
    engine = create_engine("sqlite:///backend/finlite.db", echo=False)
    models.Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    uow = SqlAlchemyUnitOfWork(session_factory)
    
    print("🏦 Criando estrutura de contas...")
    print("=" * 60)
    
    try:
        with uow:
            def ensure_account(name, account_type, currency, parent=None):
                existing = uow.accounts.find_by_name(name)
                if existing:
                    return existing
                parent_id = parent.id if parent is not None else None
                acc = Account.create(name=name, account_type=account_type, currency=currency, parent_id=parent_id)
                uow.accounts.add(acc)
                return acc

            # ============================================
            # ASSETS (Ativos)
            # ============================================
            print("\n📊 ASSETS (Ativos)")
            print("-" * 60)
            
            assets = ensure_account("Assets", AccountType.ASSET, "BRL")
            print(f"✅ {assets.name} (ID: {assets.id})")
            
            # Banks
            bank = ensure_account("Assets:Bank", AccountType.ASSET, "BRL", parent=assets)
            print(f"  ├── {bank.name}")
            
            nubank = ensure_account("Assets:Bank:Nubank", AccountType.ASSET, "BRL", parent=bank)
            print(f"  │   ├── {nubank.name}")
            
            itau = ensure_account("Assets:Bank:Itau", AccountType.ASSET, "BRL", parent=bank)
            print(f"  │   └── {itau.name}")
            
            # Cash
            cash = ensure_account("Assets:Cash", AccountType.ASSET, "BRL", parent=assets)
            print(f"  └── {cash.name}")
            
            # ============================================
            # EXPENSES (Despesas)
            # ============================================
            print("\n💸 EXPENSES (Despesas)")
            print("-" * 60)
            
            expenses = ensure_account("Expenses", AccountType.EXPENSE, "BRL")
            print(f"✅ {expenses.name}")
            
            # Food
            food = ensure_account("Expenses:Food", AccountType.EXPENSE, "BRL", parent=expenses)
            print(f"  ├── {food.name}")
            
            restaurant = ensure_account("Expenses:Food:Restaurant", AccountType.EXPENSE, "BRL", parent=food)
            print(f"  │   ├── {restaurant.name}")
            
            groceries = ensure_account("Expenses:Food:Groceries", AccountType.EXPENSE, "BRL", parent=food)
            print(f"  │   └── {groceries.name}")
            
            # Transport
            transport = ensure_account("Expenses:Transport", AccountType.EXPENSE, "BRL", parent=expenses)
            print(f"  ├── {transport.name}")
            
            uber = ensure_account("Expenses:Transport:Uber", AccountType.EXPENSE, "BRL", parent=transport)
            print(f"  │   └── {uber.name}")
            
            # Housing
            housing = ensure_account("Expenses:Housing", AccountType.EXPENSE, "BRL", parent=expenses)
            print(f"  ├── {housing.name}")
            
            rent = ensure_account("Expenses:Housing:Rent", AccountType.EXPENSE, "BRL", parent=housing)
            print(f"  │   ├── {rent.name}")
            
            utilities = ensure_account("Expenses:Housing:Utilities", AccountType.EXPENSE, "BRL", parent=housing)
            print(f"  │   └── {utilities.name}")
            
            # Entertainment
            entertainment = ensure_account("Expenses:Entertainment", AccountType.EXPENSE, "BRL", parent=expenses)
            print(f"  └── {entertainment.name}")
            
            # ============================================
            # INCOME (Receitas)
            # ============================================
            print("\n💰 INCOME (Receitas)")
            print("-" * 60)
            
            income = ensure_account("Income", AccountType.INCOME, "BRL")
            print(f"✅ {income.name}")
            
            salary = ensure_account("Income:Salary", AccountType.INCOME, "BRL", parent=income)
            print(f"  ├── {salary.name}")
            
            freelance = ensure_account("Income:Freelance", AccountType.INCOME, "BRL", parent=income)
            print(f"  └── {freelance.name}")
            
            # ============================================
            # LIABILITIES (Passivos)
            # ============================================
            print("\n💳 LIABILITIES (Passivos)")
            print("-" * 60)
            
            liabilities = ensure_account("Liabilities", AccountType.LIABILITY, "BRL")
            print(f"✅ {liabilities.name}")
            
            credit_card = ensure_account("Liabilities:CreditCard", AccountType.LIABILITY, "BRL", parent=liabilities)
            print(f"  └── {credit_card.name}")
            
            # Commit tudo
            uow.commit()
            
            print("\n" + "=" * 60)
            print("✅ Estrutura de contas criada com sucesso!")
            print("=" * 60)
            
            # Listar todas as contas criadas
            all_accounts = uow.accounts.list_all()
            print(f"\n📊 Total de contas criadas: {len(all_accounts)}")
            
            print("\n💡 Dicas:")
            print("  - Use estas contas nos próximos exemplos")
            print("  - Você pode criar mais contas conforme necessário")
            print("  - A hierarquia ajuda na organização e relatórios")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Erro ao criar contas: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # SqlAlchemyUnitOfWork context manager closes the session.
        pass


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║              FinApp - Setup de Contas                         ║
    ║                                                               ║
    ║  Este exemplo cria uma estrutura completa de contas para      ║
    ║  você começar a usar o FinApp imediatamente.                  ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    success = setup_accounts()
    
    if success:
        print("\n🎉 Próximo passo: python examples/02_create_transactions.py")
    else:
        print("\n❌ Falhou. Verifique os erros acima.")
        sys.exit(1)
