"""
Tests for Circular Buffer DSA Implementation
"""

import pytest
from app.core.dsa.circular_buffer import CircularBuffer, TimestampedCircularBuffer


class TestCircularBuffer:
    """Test suite for Circular Buffer data structure."""
    
    def test_create_buffer(self):
        """Test creating a buffer."""
        cb = CircularBuffer(capacity=5)
        
        assert len(cb) == 0
        assert cb.capacity == 5
        assert cb.is_empty
        assert not cb.is_full
    
    def test_push(self):
        """Test pushing items."""
        cb = CircularBuffer(capacity=5)
        cb.push(1)
        cb.push(2)
        cb.push(3)
        
        assert len(cb) == 3
    
    def test_push_returns_overwritten(self):
        """Test that push returns overwritten item when full."""
        cb = CircularBuffer(capacity=3)
        cb.push(1)
        cb.push(2)
        cb.push(3)
        
        overwritten = cb.push(4)
        
        assert overwritten == 1
    
    def test_pop(self):
        """Test popping oldest item."""
        cb = CircularBuffer(capacity=5)
        cb.push(1)
        cb.push(2)
        cb.push(3)
        
        result = cb.pop()
        
        assert result == 1
        assert len(cb) == 2
    
    def test_pop_empty(self):
        """Test popping from empty buffer."""
        cb = CircularBuffer(capacity=5)
        
        assert cb.pop() is None
    
    def test_peek_oldest(self):
        """Test peeking at oldest."""
        cb = CircularBuffer(capacity=5)
        cb.push(1)
        cb.push(2)
        
        result = cb.peek_oldest()
        
        assert result == 1
        assert len(cb) == 2  # Peek doesn't remove
    
    def test_peek_newest(self):
        """Test peeking at newest."""
        cb = CircularBuffer(capacity=5)
        cb.push(1)
        cb.push(2)
        
        result = cb.peek_newest()
        
        assert result == 2
    
    def test_wrap_around(self):
        """Test that buffer wraps around correctly."""
        cb = CircularBuffer(capacity=3)
        cb.push(1)
        cb.push(2)
        cb.push(3)
        cb.push(4)  # Overwrites 1
        cb.push(5)  # Overwrites 2
        
        assert len(cb) == 3
        assert cb.get_all() == [3, 4, 5]
    
    def test_getitem(self):
        """Test bracket access."""
        cb = CircularBuffer(capacity=5)
        cb.push(1)
        cb.push(2)
        cb.push(3)
        
        assert cb[0] == 1  # Oldest
        assert cb[2] == 3  # Newest
        assert cb[-1] == 3  # Negative index
    
    def test_iteration(self):
        """Test iterating over buffer."""
        cb = CircularBuffer(capacity=5)
        cb.push(1)
        cb.push(2)
        cb.push(3)
        
        result = list(cb)
        
        assert result == [1, 2, 3]
    
    def test_push_many(self):
        """Test pushing multiple items."""
        cb = CircularBuffer(capacity=3)
        
        overwritten = cb.push_many([1, 2, 3, 4])
        
        assert overwritten == [1]
        assert cb.get_all() == [2, 3, 4]
    
    def test_pop_many(self):
        """Test popping multiple items."""
        cb = CircularBuffer(capacity=5)
        cb.push_many([1, 2, 3, 4, 5])
        
        result = cb.pop_many(3)
        
        assert result == [1, 2, 3]
        assert len(cb) == 2
    
    def test_get_all(self):
        """Test getting all items."""
        cb = CircularBuffer(capacity=5)
        cb.push(1)
        cb.push(2)
        cb.push(3)
        
        result = cb.get_all()
        
        assert result == [1, 2, 3]
    
    def test_get_last_n(self):
        """Test getting last N items."""
        cb = CircularBuffer(capacity=5)
        cb.push_many([1, 2, 3, 4, 5])
        
        result = cb.get_last_n(3)
        
        assert result == [3, 4, 5]
    
    def test_get_first_n(self):
        """Test getting first N items."""
        cb = CircularBuffer(capacity=5)
        cb.push_many([1, 2, 3, 4, 5])
        
        result = cb.get_first_n(3)
        
        assert result == [1, 2, 3]
    
    def test_is_full(self):
        """Test is_full property."""
        cb = CircularBuffer(capacity=3)
        
        assert not cb.is_full
        
        cb.push(1)
        cb.push(2)
        cb.push(3)
        
        assert cb.is_full
    
    def test_clear(self):
        """Test clearing buffer."""
        cb = CircularBuffer(capacity=5)
        cb.push(1)
        cb.push(2)
        
        cb.clear()
        
        assert len(cb) == 0
        assert cb.is_empty
    
    def test_resize(self):
        """Test resizing buffer."""
        cb = CircularBuffer(capacity=3)
        cb.push_many([1, 2, 3])
        
        cb.resize(5)
        
        assert cb.capacity == 5
        assert cb.get_all() == [1, 2, 3]
        
        # Resize smaller
        cb.resize(2)
        assert cb.capacity == 2
    
    def test_stats(self):
        """Test getting statistics."""
        cb = CircularBuffer(capacity=5)
        cb.push(1)
        cb.push(2)
        
        stats = cb.stats()
        
        assert stats["capacity"] == 5
        assert stats["size"] == 2
        assert not stats["is_full"]
    
    def test_invalid_capacity(self):
        """Test that invalid capacity raises error."""
        with pytest.raises(ValueError):
            CircularBuffer(capacity=0)
        
        with pytest.raises(ValueError):
            CircularBuffer(capacity=-1)


class TestTimestampedCircularBuffer:
    """Test suite for Timestamped Circular Buffer."""
    
    def test_push_with_time(self):
        """Test pushing with timestamp."""
        cb = TimestampedCircularBuffer(capacity=5)
        cb.push_with_time("item1", timestamp=1000.0)
        cb.push_with_time("item2", timestamp=2000.0)
        
        assert len(cb) == 2
    
    def test_get_items_since(self):
        """Test getting items since timestamp."""
        cb = TimestampedCircularBuffer(capacity=5)
        cb.push_with_time("item1", timestamp=1000.0)
        cb.push_with_time("item2", timestamp=2000.0)
        cb.push_with_time("item3", timestamp=3000.0)
        
        items = cb.get_items_since(1500.0)
        
        assert len(items) == 2
        assert "item2" in items
        assert "item3" in items


