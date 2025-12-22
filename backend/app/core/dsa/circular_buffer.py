"""Circular Buffer implementation.

This module implements a circular buffer (ring buffer) with fixed capacity.
Automatically overwrites oldest items when full, making it ideal for
rolling event logs and time-windowed data storage.

DSA Concept: Circular Buffer
- Fixed-size buffer with automatic overwrite
- O(1) push, pop, and access operations
- Time-windowed variant support
- Ideal for rolling event logs and real-time traffic analysis
"""

from typing import Any, Optional, List, Generator
from dataclasses import dataclass


class CircularBuffer:
    
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        self._capacity = capacity
        self._buffer: List[Any] = [None] * capacity
        self._head = 0
        self._tail = 0
        self._size = 0
        self._total_items_added = 0
    
    def __len__(self) -> int:
        return self._size
    
    def __bool__(self) -> bool:
        return self._size > 0
    
    def __iter__(self) -> Generator[Any, None, None]:
        for i in range(self._size):
            index = (self._tail + i) % self._capacity
            yield self._buffer[index]
    
    def __getitem__(self, index: int) -> Any:
        if index < 0:
            index += self._size
        
        if index < 0 or index >= self._size:
            raise IndexError("Index out of range")
        
        actual_index = (self._tail + index) % self._capacity
        return self._buffer[actual_index]
    
    @property
    def capacity(self) -> int:
        return self._capacity
    
    @property
    def is_full(self) -> bool:
        return self._size == self._capacity
    
    @property
    def is_empty(self) -> bool:
        return self._size == 0
    
    def push(self, item: Any) -> Optional[Any]:
        """Add an item to the buffer, overwriting oldest if full.
        
        Args:
            item: Item to add
        
        Returns:
            Overwritten item if buffer was full, None otherwise
        """
        overwritten = None
        
        if self._size == self._capacity:
            overwritten = self._buffer[self._tail]
            self._tail = (self._tail + 1) % self._capacity
        else:
            self._size += 1
        
        self._buffer[self._head] = item
        self._head = (self._head + 1) % self._capacity
        self._total_items_added += 1
        
        return overwritten
    
    def pop(self) -> Optional[Any]:
        """Remove and return the oldest item from the buffer.
        
        Returns:
            Oldest item, or None if buffer is empty
        """
        if self._size == 0:
            return None
        
        item = self._buffer[self._tail]
        self._buffer[self._tail] = None
        self._tail = (self._tail + 1) % self._capacity
        self._size -= 1
        
        return item
    
    def peek_oldest(self) -> Optional[Any]:
        """Get the oldest item without removing it.
        
        Returns:
            Oldest item, or None if buffer is empty
        """
        if self._size == 0:
            return None
        return self._buffer[self._tail]
    
    def peek_newest(self) -> Optional[Any]:
        """Get the newest item without removing it.
        
        Returns:
            Newest item, or None if buffer is empty
        """
        if self._size == 0:
            return None
        index = (self._head - 1) % self._capacity
        return self._buffer[index]
    
    def push_many(self, items: List[Any]) -> List[Any]:
        """Add multiple items to the buffer.
        
        Args:
            items: List of items to add
        
        Returns:
            List of overwritten items
        """
        overwritten = []
        for item in items:
            result = self.push(item)
            if result is not None:
                overwritten.append(result)
        return overwritten
    
    def pop_many(self, n: int) -> List[Any]:
        """Remove and return multiple items from the buffer.
        
        Args:
            n: Number of items to pop
        
        Returns:
            List of popped items
        """
        result = []
        for _ in range(min(n, self._size)):
            item = self.pop()
            if item is not None:
                result.append(item)
        return result
    
    def get_all(self) -> List[Any]:
        """Get all items in the buffer in order.
        
        Returns:
            List of all items from oldest to newest
        """
        return list(self)
    
    def get_last_n(self, n: int) -> List[Any]:
        """Get the last N items (newest items).
        
        Args:
            n: Number of newest items to retrieve
        
        Returns:
            List of the newest N items
        """
        if n >= self._size:
            return self.get_all()
        
        result = []
        start = (self._head - n) % self._capacity
        for i in range(n):
            index = (start + i) % self._capacity
            result.append(self._buffer[index])
        return result
    
    def get_first_n(self, n: int) -> List[Any]:
        """Get the first N items (oldest items).
        
        Args:
            n: Number of oldest items to retrieve
        
        Returns:
            List of the oldest N items
        """
        if n >= self._size:
            return self.get_all()
        
        result = []
        for i in range(n):
            index = (self._tail + i) % self._capacity
            result.append(self._buffer[index])
        return result
    
    def clear(self):
        """Remove all items from the buffer."""
        self._buffer = [None] * self._capacity
        self._head = 0
        self._tail = 0
        self._size = 0
    
    def resize(self, new_capacity: int):
        """Resize the buffer to a new capacity.
        
        Args:
            new_capacity: New capacity for the buffer
        
        Raises:
            ValueError: If new_capacity is not positive
        """
        if new_capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        items = self.get_all()
        
        self._capacity = new_capacity
        self._buffer = [None] * new_capacity
        self._head = 0
        self._tail = 0
        self._size = 0
        
        for item in items:
            self.push(item)
    
    def stats(self) -> dict:
        """Get statistics about the buffer.
        
        Returns:
            Dictionary with buffer statistics
        """
        return {
            "capacity": self._capacity,
            "size": self._size,
            "is_full": self.is_full,
            "utilization": self._size / self._capacity,
            "total_items_added": self._total_items_added,
            "overwrite_count": max(0, self._total_items_added - self._capacity)
        }


class TimestampedCircularBuffer(CircularBuffer):
    
    @dataclass
    class TimestampedItem:
        timestamp: float
        data: Any
    
    def __init__(self, capacity: int):
        super().__init__(capacity)
    
    def push_with_time(self, item: Any, timestamp: float = None) -> Optional[Any]:
        """Add an item with a timestamp to the buffer.
        
        Args:
            item: Item to add
            timestamp: Optional timestamp (defaults to current time)
        
        Returns:
            Overwritten item if buffer was full, None otherwise
        """
        import time
        if timestamp is None:
            timestamp = time.time()
        
        timestamped = self.TimestampedItem(timestamp=timestamp, data=item)
        return super().push(timestamped)
    
    def get_items_since(self, since_timestamp: float) -> List[Any]:
        result = []
        for item in self:
            if isinstance(item, self.TimestampedItem) and item.timestamp >= since_timestamp:
                result.append(item.data)
        return result
    
    def get_items_in_window(self, window_seconds: float) -> List[Any]:
        """Get all items within a time window from now.
        
        Args:
            window_seconds: Time window in seconds
        
        Returns:
            List of items within the time window
        """
        import time
        cutoff = time.time() - window_seconds
        return self.get_items_since(cutoff)
    
    def expire_old(self, max_age_seconds: float) -> int:
        """Remove items older than the specified age.
        
        Args:
            max_age_seconds: Maximum age in seconds
        
        Returns:
            Number of items removed
        """
        import time
        cutoff = time.time() - max_age_seconds
        removed = 0
        
        while self._size > 0:
            oldest = self.peek_oldest()
            if isinstance(oldest, self.TimestampedItem) and oldest.timestamp < cutoff:
                self.pop()
                removed += 1
            else:
                break
        
        return removed


