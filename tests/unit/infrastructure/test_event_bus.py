"""Unit tests for Event Bus."""

import pytest
from uuid import uuid4

from finlite.infrastructure.events import InMemoryEventBus, EventHandler
from finlite.domain.events import DomainEvent, AccountCreated, TransactionRecorded
from datetime import date
from decimal import Decimal


class TestInMemoryEventBus:
    """Test suite for InMemoryEventBus."""
    
    @pytest.fixture
    def event_bus(self):
        """Create event bus instance."""
        return InMemoryEventBus()
    
    @pytest.fixture
    def sample_account_event(self):
        """Create sample account event."""
        return AccountCreated(
            account_id=uuid4(),
            account_code="TEST001",
            account_type="ASSET",
            currency="USD"
        )
    
    def test_subscribe_and_publish(self, event_bus, sample_account_event):
        """Test basic subscribe and publish."""
        # Track if handler was called
        calls = []
        
        def handler(event):
            calls.append(event)
        
        # Subscribe
        event_bus.subscribe(AccountCreated, handler)
        
        # Publish
        event_bus.publish(sample_account_event)
        
        # Assert handler was called
        assert len(calls) == 1
        assert calls[0] == sample_account_event
    
    def test_multiple_handlers(self, event_bus, sample_account_event):
        """Test multiple handlers for same event type."""
        calls1 = []
        calls2 = []
        
        def handler1(event):
            calls1.append(event)
        
        def handler2(event):
            calls2.append(event)
        
        # Subscribe both handlers
        event_bus.subscribe(AccountCreated, handler1)
        event_bus.subscribe(AccountCreated, handler2)
        
        # Publish
        event_bus.publish(sample_account_event)
        
        # Assert both handlers were called
        assert len(calls1) == 1
        assert len(calls2) == 1
    
    def test_unsubscribe(self, event_bus, sample_account_event):
        """Test unsubscribing a handler."""
        calls = []
        
        def handler(event):
            calls.append(event)
        
        # Subscribe
        event_bus.subscribe(AccountCreated, handler)
        
        # Publish (should work)
        event_bus.publish(sample_account_event)
        assert len(calls) == 1
        
        # Unsubscribe
        event_bus.unsubscribe(AccountCreated, handler)
        
        # Publish again (should not call handler)
        event_bus.publish(sample_account_event)
        assert len(calls) == 1  # Still 1, not 2
    
    def test_clear_all_subscriptions(self, event_bus, sample_account_event):
        """Test clearing all subscriptions."""
        calls = []
        
        def handler(event):
            calls.append(event)
        
        # Subscribe
        event_bus.subscribe(AccountCreated, handler)
        
        # Clear
        event_bus.clear()
        
        # Publish (should not call handler)
        event_bus.publish(sample_account_event)
        assert len(calls) == 0
    
    def test_different_event_types(self, event_bus):
        """Test that different event types are handled separately."""
        account_calls = []
        transaction_calls = []
        
        def account_handler(event):
            account_calls.append(event)
        
        def transaction_handler(event):
            transaction_calls.append(event)
        
        # Subscribe to different event types
        event_bus.subscribe(AccountCreated, account_handler)
        event_bus.subscribe(TransactionRecorded, transaction_handler)
        
        # Publish account event
        account_event = AccountCreated(
            account_id=uuid4(),
            account_code="TEST001",
            account_type="ASSET",
            currency="USD"
        )
        event_bus.publish(account_event)
        
        # Publish transaction event
        transaction_event = TransactionRecorded(
            transaction_id=uuid4(),
            transaction_date=date(2025, 1, 15),
            description="Test transaction",
            total_amount=Decimal("0"),
            posting_count=2,
            affected_accounts=(uuid4(), uuid4())
        )
        event_bus.publish(transaction_event)
        
        # Assert correct handlers were called
        assert len(account_calls) == 1
        assert len(transaction_calls) == 1
        assert account_calls[0] == account_event
        assert transaction_calls[0] == transaction_event
    
    def test_handler_exception_doesnt_stop_others(self, event_bus, sample_account_event, capsys):
        """Test that exception in one handler doesn't stop others."""
        calls = []
        
        def failing_handler(event):
            raise ValueError("Handler failed")
        
        def working_handler(event):
            calls.append(event)
        
        # Subscribe both handlers
        event_bus.subscribe(AccountCreated, failing_handler)
        event_bus.subscribe(AccountCreated, working_handler)
        
        # Publish (failing handler should not stop working handler)
        event_bus.publish(sample_account_event)
        
        # Assert working handler was still called
        assert len(calls) == 1
        
        # Check that error was printed
        captured = capsys.readouterr()
        assert "Error handling event" in captured.out
    
    def test_get_handlers(self, event_bus):
        """Test getting handlers for an event type."""
        def handler1(event):
            pass
        
        def handler2(event):
            pass
        
        # Subscribe handlers
        event_bus.subscribe(AccountCreated, handler1)
        event_bus.subscribe(AccountCreated, handler2)
        
        # Get handlers
        handlers = event_bus.get_handlers(AccountCreated)
        
        assert len(handlers) == 2
        assert handler1 in handlers
        assert handler2 in handlers
    
    def test_duplicate_subscription_ignored(self, event_bus, sample_account_event):
        """Test that subscribing same handler twice is ignored."""
        calls = []
        
        def handler(event):
            calls.append(event)
        
        # Subscribe same handler twice
        event_bus.subscribe(AccountCreated, handler)
        event_bus.subscribe(AccountCreated, handler)
        
        # Publish
        event_bus.publish(sample_account_event)
        
        # Assert handler was called only once
        assert len(calls) == 1


class TestDomainEvents:
    """Test suite for domain events."""
    
    def test_account_created_event(self):
        """Test AccountCreated event."""
        account_id = uuid4()
        event = AccountCreated(
            account_id=account_id,
            account_code="CASH001",
            account_type="ASSET",
            currency="USD"
        )
        
        assert event.account_id == account_id
        assert event.account_code == "CASH001"
        assert event.account_type == "ASSET"
        assert event.currency == "USD"
        assert event.event_type == "AccountCreated"
        assert event.event_id is not None
        assert event.occurred_at is not None
    
    def test_transaction_recorded_event(self):
        """Test TransactionRecorded event."""
        transaction_id = uuid4()
        account1_id = uuid4()
        account2_id = uuid4()
        
        event = TransactionRecorded(
            transaction_id=transaction_id,
            transaction_date=date(2025, 1, 15),
            description="Test transaction",
            total_amount=Decimal("0"),
            posting_count=2,
            affected_accounts=(account1_id, account2_id)
        )
        
        assert event.transaction_id == transaction_id
        assert event.transaction_date == date(2025, 1, 15)
        assert event.description == "Test transaction"
        assert event.total_amount == Decimal("0")
        assert event.posting_count == 2
        assert len(event.affected_accounts) == 2
        assert event.event_type == "TransactionRecorded"
    
    def test_event_immutability(self):
        """Test that events are immutable (frozen)."""
        event = AccountCreated(
            account_id=uuid4(),
            account_code="TEST001",
            account_type="ASSET",
            currency="USD"
        )
        
        # Try to modify (should fail)
        with pytest.raises(Exception):  # FrozenInstanceError
            event.account_code = "MODIFIED"
