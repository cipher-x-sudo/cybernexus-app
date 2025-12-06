"""
Custom Heap Implementations

Binary Heap (Min and Max) for priority-based operations.

Used for:
- Threat severity ranking
- Alert priority queues
- Anomaly scoring
"""

from typing import Any, Optional, List, Tuple, Generator, Callable
from dataclasses import dataclass


@dataclass
class HeapItem:
    """Item in the heap with priority and value."""
    priority: float
    value: Any
    
    def __lt__(self, other: "HeapItem") -> bool:
        return self.priority < other.priority
    
    def __le__(self, other: "HeapItem") -> bool:
        return self.priority <= other.priority
    
    def __gt__(self, other: "HeapItem") -> bool:
        return self.priority > other.priority
    
    def __ge__(self, other: "HeapItem") -> bool:
        return self.priority >= other.priority


class MinHeap:
    """
    Min-Heap Implementation (smallest element at top).
    
    Features:
    - O(log n) insert and extract_min
    - O(1) peek at minimum
    - Heapify operation
    - Supports priority/value pairs
    """
    
    def __init__(self):
        """Initialize empty min-heap."""
        self._heap: List[HeapItem] = []
    
    def __len__(self) -> int:
        return len(self._heap)
    
    def __bool__(self) -> bool:
        return len(self._heap) > 0
    
    # ==================== Index Helpers ====================
    
    def _parent(self, i: int) -> int:
        """Get parent index."""
        return (i - 1) // 2
    
    def _left_child(self, i: int) -> int:
        """Get left child index."""
        return 2 * i + 1
    
    def _right_child(self, i: int) -> int:
        """Get right child index."""
        return 2 * i + 2
    
    def _has_parent(self, i: int) -> bool:
        return self._parent(i) >= 0
    
    def _has_left_child(self, i: int) -> bool:
        return self._left_child(i) < len(self._heap)
    
    def _has_right_child(self, i: int) -> bool:
        return self._right_child(i) < len(self._heap)
    
    def _swap(self, i: int, j: int):
        """Swap elements at indices i and j."""
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
    
    # ==================== Heap Operations ====================
    
    def _sift_up(self, i: int):
        """Move element up to maintain heap property."""
        while self._has_parent(i) and self._heap[self._parent(i)] > self._heap[i]:
            parent_idx = self._parent(i)
            self._swap(i, parent_idx)
            i = parent_idx
    
    def _sift_down(self, i: int):
        """Move element down to maintain heap property."""
        while self._has_left_child(i):
            smaller_child_idx = self._left_child(i)
            
            if (self._has_right_child(i) and 
                self._heap[self._right_child(i)] < self._heap[smaller_child_idx]):
                smaller_child_idx = self._right_child(i)
            
            if self._heap[i] <= self._heap[smaller_child_idx]:
                break
            
            self._swap(i, smaller_child_idx)
            i = smaller_child_idx
    
    # ==================== Public Methods ====================
    
    def push(self, priority: float, value: Any = None):
        """Insert an element into the heap.
        
        Args:
            priority: Priority value (lower = higher priority for min-heap)
            value: Associated value (defaults to priority)
        """
        if value is None:
            value = priority
        
        item = HeapItem(priority=priority, value=value)
        self._heap.append(item)
        self._sift_up(len(self._heap) - 1)
    
    def pop(self) -> Optional[Tuple[float, Any]]:
        """Remove and return the minimum element.
        
        Returns:
            Tuple of (priority, value) or None if empty
        """
        if not self._heap:
            return None
        
        min_item = self._heap[0]
        last_item = self._heap.pop()
        
        if self._heap:
            self._heap[0] = last_item
            self._sift_down(0)
        
        return (min_item.priority, min_item.value)
    
    def peek(self) -> Optional[Tuple[float, Any]]:
        """Return the minimum element without removing it.
        
        Returns:
            Tuple of (priority, value) or None if empty
        """
        if not self._heap:
            return None
        return (self._heap[0].priority, self._heap[0].value)
    
    def push_pop(self, priority: float, value: Any = None) -> Tuple[float, Any]:
        """Push new element and pop minimum. More efficient than separate operations."""
        if value is None:
            value = priority
        
        if not self._heap:
            return (priority, value)
        
        if priority <= self._heap[0].priority:
            return (priority, value)
        
        min_item = self._heap[0]
        self._heap[0] = HeapItem(priority=priority, value=value)
        self._sift_down(0)
        
        return (min_item.priority, min_item.value)
    
    def replace(self, priority: float, value: Any = None) -> Optional[Tuple[float, Any]]:
        """Pop minimum and push new element. More efficient than separate operations."""
        if value is None:
            value = priority
        
        if not self._heap:
            self.push(priority, value)
            return None
        
        min_item = self._heap[0]
        self._heap[0] = HeapItem(priority=priority, value=value)
        self._sift_down(0)
        
        return (min_item.priority, min_item.value)
    
    def heapify(self, items: List[Tuple[float, Any]]):
        """Build heap from list of (priority, value) tuples in O(n) time."""
        self._heap = [HeapItem(priority=p, value=v) for p, v in items]
        
        # Start from last non-leaf node and sift down
        for i in range(len(self._heap) // 2 - 1, -1, -1):
            self._sift_down(i)
    
    def get_top_n(self, n: int) -> List[Tuple[float, Any]]:
        """Get top N elements (smallest N for min-heap).
        
        Note: This removes elements from the heap.
        """
        result = []
        for _ in range(min(n, len(self._heap))):
            item = self.pop()
            if item:
                result.append(item)
        return result
    
    def clear(self):
        """Remove all elements."""
        self._heap.clear()
    
    def to_list(self) -> List[Tuple[float, Any]]:
        """Convert heap to list of (priority, value) tuples."""
        return [(item.priority, item.value) for item in self._heap]


class MaxHeap:
    """
    Max-Heap Implementation (largest element at top).
    
    Implemented as a min-heap with negated priorities for efficiency.
    """
    
    def __init__(self):
        """Initialize empty max-heap."""
        self._min_heap = MinHeap()
    
    def __len__(self) -> int:
        return len(self._min_heap)
    
    def __bool__(self) -> bool:
        return bool(self._min_heap)
    
    def push(self, priority: float, value: Any = None):
        """Insert an element into the heap.
        
        Args:
            priority: Priority value (higher = higher priority for max-heap)
            value: Associated value (defaults to priority)
        """
        self._min_heap.push(-priority, value if value is not None else priority)
    
    def pop(self) -> Optional[Tuple[float, Any]]:
        """Remove and return the maximum element.
        
        Returns:
            Tuple of (priority, value) or None if empty
        """
        result = self._min_heap.pop()
        if result:
            return (-result[0], result[1])
        return None
    
    def peek(self) -> Optional[Tuple[float, Any]]:
        """Return the maximum element without removing it.
        
        Returns:
            Tuple of (priority, value) or None if empty
        """
        result = self._min_heap.peek()
        if result:
            return (-result[0], result[1])
        return None
    
    def push_pop(self, priority: float, value: Any = None) -> Tuple[float, Any]:
        """Push new element and pop maximum."""
        result = self._min_heap.push_pop(-priority, value if value is not None else priority)
        return (-result[0], result[1])
    
    def heapify(self, items: List[Tuple[float, Any]]):
        """Build heap from list of (priority, value) tuples."""
        negated = [(-p, v) for p, v in items]
        self._min_heap.heapify(negated)
    
    def get_top_n(self, n: int) -> List[Tuple[float, Any]]:
        """Get top N elements (largest N for max-heap)."""
        result = self._min_heap.get_top_n(n)
        return [(-p, v) for p, v in result]
    
    def clear(self):
        """Remove all elements."""
        self._min_heap.clear()
    
    def to_list(self) -> List[Tuple[float, Any]]:
        """Convert heap to list of (priority, value) tuples."""
        return [(-item.priority, item.value) for item in self._min_heap._heap]


class PriorityQueue:
    """
    Priority Queue with update capability.
    
    Supports updating priority of existing items.
    Used for Dijkstra's algorithm and threat ranking with dynamic priorities.
    """
    
    def __init__(self, min_queue: bool = True):
        """Initialize priority queue.
        
        Args:
            min_queue: If True, lower priority values have higher priority
        """
        self._heap = MinHeap() if min_queue else MaxHeap()
        self._entry_finder = {}  # Maps value to its current heap item
        self._counter = 0  # Unique sequence number for ties
        self._REMOVED = object()  # Marker for removed items
    
    def __len__(self) -> int:
        return len(self._entry_finder)
    
    def __bool__(self) -> bool:
        return len(self._entry_finder) > 0
    
    def __contains__(self, value: Any) -> bool:
        return value in self._entry_finder
    
    def add(self, value: Any, priority: float):
        """Add or update an item in the queue."""
        if value in self._entry_finder:
            self.remove(value)
        
        entry = [priority, self._counter, value]
        self._entry_finder[value] = entry
        self._heap.push(priority, entry)
        self._counter += 1
    
    def remove(self, value: Any) -> bool:
        """Remove an item from the queue."""
        entry = self._entry_finder.pop(value, None)
        if entry:
            entry[-1] = self._REMOVED
            return True
        return False
    
    def pop(self) -> Optional[Tuple[float, Any]]:
        """Remove and return item with highest priority."""
        while self._heap:
            result = self._heap.pop()
            if result:
                priority, entry = result
                if isinstance(entry, list) and entry[-1] is not self._REMOVED:
                    value = entry[-1]
                    del self._entry_finder[value]
                    return (priority, value)
        return None
    
    def peek(self) -> Optional[Tuple[float, Any]]:
        """Return item with highest priority without removing it."""
        # This is trickier with lazy removal - need to find actual top
        while self._heap:
            result = self._heap.peek()
            if result:
                priority, entry = result
                if isinstance(entry, list) and entry[-1] is not self._REMOVED:
                    return (priority, entry[-1])
                # Remove marked item
                self._heap.pop()
        return None
    
    def update_priority(self, value: Any, new_priority: float):
        """Update the priority of an existing item."""
        self.add(value, new_priority)
    
    def get_priority(self, value: Any) -> Optional[float]:
        """Get the current priority of an item."""
        entry = self._entry_finder.get(value)
        if entry and entry[-1] is not self._REMOVED:
            return entry[0]
        return None


