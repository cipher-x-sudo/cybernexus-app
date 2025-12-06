"""
Custom Circular Buffer Implementation

Fixed-size ring buffer for streaming data with automatic overwrite of oldest items.

Used for:
- Rolling event logs
- Real-time traffic analysis windows
- Recent activity tracking
"""

from typing import Any, Optional, List, Generator
from dataclasses import dataclass


class CircularBuffer:
    """
    Circular Buffer (Ring Buffer) Implementation.
    
    Features:
    - Fixed-size buffer that wraps around
    - O(1) push and pop operations
    - Automatic overwrite of oldest items when full
    - Efficient for streaming/windowed data
    """
    
    def __init__(self, capacity: int):
        """Initialize circular buffer.
        
        Args:
            capacity: Maximum number of items to store
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        self._capacity = capacity
        self._buffer: List[Any] = [None] * capacity
        self._head = 0  # Next write position
        self._tail = 0  # Next read position
        self._size = 0
        self._total_items_added = 0  # Track total items ever added (for statistics)
    
    def __len__(self) -> int:
        return self._size
    
    def __bool__(self) -> bool:
        return self._size > 0
    
    def __iter__(self) -> Generator[Any, None, None]:
        """Iterate from oldest to newest."""
        for i in range(self._size):
            index = (self._tail + i) % self._capacity
            yield self._buffer[index]
    
    def __getitem__(self, index: int) -> Any:
        """Get item by index (0 = oldest)."""
        if index < 0:
            index += self._size
        
        if index < 0 or index >= self._size:
            raise IndexError("Index out of range")
        
        actual_index = (self._tail + index) % self._capacity
        return self._buffer[actual_index]
    
    @property
    def capacity(self) -> int:
        """Get buffer capacity."""
        return self._capacity
    
    @property
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return self._size == self._capacity
    
    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return self._size == 0
    
    # ==================== Core Operations ====================
    
    def push(self, item: Any) -> Optional[Any]:
        """Add item to buffer.
        
        Args:
            item: Item to add
            
        Returns:
            The overwritten item if buffer was full, None otherwise
        """
        overwritten = None
        
        if self._size == self._capacity:
            # Buffer is full, overwrite oldest
            overwritten = self._buffer[self._tail]
            self._tail = (self._tail + 1) % self._capacity
        else:
            self._size += 1
        
        self._buffer[self._head] = item
        self._head = (self._head + 1) % self._capacity
        self._total_items_added += 1
        
        return overwritten
    
    def pop(self) -> Optional[Any]:
        """Remove and return oldest item.
        
        Returns:
            The oldest item, or None if buffer is empty
        """
        if self._size == 0:
            return None
        
        item = self._buffer[self._tail]
        self._buffer[self._tail] = None  # Help GC
        self._tail = (self._tail + 1) % self._capacity
        self._size -= 1
        
        return item
    
    def peek_oldest(self) -> Optional[Any]:
        """Get oldest item without removing it."""
        if self._size == 0:
            return None
        return self._buffer[self._tail]
    
    def peek_newest(self) -> Optional[Any]:
        """Get newest item without removing it."""
        if self._size == 0:
            return None
        index = (self._head - 1) % self._capacity
        return self._buffer[index]
    
    def push_many(self, items: List[Any]) -> List[Any]:
        """Push multiple items.
        
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
        """Pop up to n items.
        
        Returns:
            List of popped items (oldest first)
        """
        result = []
        for _ in range(min(n, self._size)):
            item = self.pop()
            if item is not None:
                result.append(item)
        return result
    
    # ==================== Access Methods ====================
    
    def get_all(self) -> List[Any]:
        """Get all items (oldest to newest)."""
        return list(self)
    
    def get_last_n(self, n: int) -> List[Any]:
        """Get last n items (most recent)."""
        if n >= self._size:
            return self.get_all()
        
        result = []
        start = (self._head - n) % self._capacity
        for i in range(n):
            index = (start + i) % self._capacity
            result.append(self._buffer[index])
        return result
    
    def get_first_n(self, n: int) -> List[Any]:
        """Get first n items (oldest)."""
        if n >= self._size:
            return self.get_all()
        
        result = []
        for i in range(n):
            index = (self._tail + i) % self._capacity
            result.append(self._buffer[index])
        return result
    
    # ==================== Utility ====================
    
    def clear(self):
        """Remove all items."""
        self._buffer = [None] * self._capacity
        self._head = 0
        self._tail = 0
        self._size = 0
    
    def resize(self, new_capacity: int):
        """Resize the buffer.
        
        Args:
            new_capacity: New capacity
        """
        if new_capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        # Get all current items
        items = self.get_all()
        
        # Reinitialize with new capacity
        self._capacity = new_capacity
        self._buffer = [None] * new_capacity
        self._head = 0
        self._tail = 0
        self._size = 0
        
        # Re-add items (will overwrite oldest if new capacity is smaller)
        for item in items:
            self.push(item)
    
    def stats(self) -> dict:
        """Get buffer statistics."""
        return {
            "capacity": self._capacity,
            "size": self._size,
            "is_full": self.is_full,
            "utilization": self._size / self._capacity,
            "total_items_added": self._total_items_added,
            "overwrite_count": max(0, self._total_items_added - self._capacity)
        }


class TimestampedCircularBuffer(CircularBuffer):
    """
    Circular buffer with timestamps for time-based operations.
    """
    
    @dataclass
    class TimestampedItem:
        timestamp: float
        data: Any
    
    def __init__(self, capacity: int):
        super().__init__(capacity)
    
    def push_with_time(self, item: Any, timestamp: float = None) -> Optional[Any]:
        """Push item with timestamp.
        
        Args:
            item: Item to add
            timestamp: Optional timestamp (defaults to current time)
        """
        import time
        if timestamp is None:
            timestamp = time.time()
        
        timestamped = self.TimestampedItem(timestamp=timestamp, data=item)
        return super().push(timestamped)
    
    def get_items_since(self, since_timestamp: float) -> List[Any]:
        """Get items added after given timestamp."""
        result = []
        for item in self:
            if isinstance(item, self.TimestampedItem) and item.timestamp >= since_timestamp:
                result.append(item.data)
        return result
    
    def get_items_in_window(self, window_seconds: float) -> List[Any]:
        """Get items within the last N seconds."""
        import time
        cutoff = time.time() - window_seconds
        return self.get_items_since(cutoff)
    
    def expire_old(self, max_age_seconds: float) -> int:
        """Remove items older than max_age_seconds.
        
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


