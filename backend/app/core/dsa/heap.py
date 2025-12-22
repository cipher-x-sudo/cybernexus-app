"""Binary Min/Max Heap implementation.

This module implements both min-heap and max-heap variants of a binary heap.
Used for priority queue operations and efficient top-N element retrieval.

DSA Concept: Binary Heap (Min/Max)
- Min-heap and max-heap variants
- Priority queue operations
- Efficient top-N retrieval
- O(log n) insert and extract operations
- O(1) peek operation
- O(n) heapify operation
"""

from typing import Any, Optional, List, Tuple, Generator, Callable
from dataclasses import dataclass


@dataclass
class HeapItem:
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
    
    def __init__(self):
        self._heap: List[HeapItem] = []
    
    def __len__(self) -> int:
        return len(self._heap)
    
    def __bool__(self) -> bool:
        return len(self._heap) > 0
    
    def _parent(self, i: int) -> int:
        return (i - 1) // 2
    
    def _left_child(self, i: int) -> int:
        return 2 * i + 1
    
    def _right_child(self, i: int) -> int:
        return 2 * i + 2
    
    def _has_parent(self, i: int) -> bool:
        return self._parent(i) >= 0
    
    def _has_left_child(self, i: int) -> bool:
        return self._left_child(i) < len(self._heap)
    
    def _has_right_child(self, i: int) -> bool:
        return self._right_child(i) < len(self._heap)
    
    def _swap(self, i: int, j: int):
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
    
    def _sift_up(self, i: int):
        while self._has_parent(i) and self._heap[self._parent(i)] > self._heap[i]:
            parent_idx = self._parent(i)
            self._swap(i, parent_idx)
            i = parent_idx
    
    def _sift_down(self, i: int):
        while self._has_left_child(i):
            smaller_child_idx = self._left_child(i)
            
            if (self._has_right_child(i) and 
                self._heap[self._right_child(i)] < self._heap[smaller_child_idx]):
                smaller_child_idx = self._right_child(i)
            
            if self._heap[i] <= self._heap[smaller_child_idx]:
                break
            
            self._swap(i, smaller_child_idx)
            i = smaller_child_idx
    
    def push(self, priority: float, value: Any = None):
        if value is None:
            value = priority
        
        item = HeapItem(priority=priority, value=value)
        self._heap.append(item)
        self._sift_up(len(self._heap) - 1)
    
    def pop(self) -> Optional[Tuple[float, Any]]:
        if not self._heap:
            return None
        
        min_item = self._heap[0]
        last_item = self._heap.pop()
        
        if self._heap:
            self._heap[0] = last_item
            self._sift_down(0)
        
        return (min_item.priority, min_item.value)
    
    def peek(self) -> Optional[Tuple[float, Any]]:
        if not self._heap:
            return None
        return (self._heap[0].priority, self._heap[0].value)
    
    def push_pop(self, priority: float, value: Any = None) -> Tuple[float, Any]:
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
        self._heap = [HeapItem(priority=p, value=v) for p, v in items]
        
        for i in range(len(self._heap) // 2 - 1, -1, -1):
            self._sift_down(i)
    
    def get_top_n(self, n: int) -> List[Tuple[float, Any]]:
        result = []
        for _ in range(min(n, len(self._heap))):
            item = self.pop()
            if item:
                result.append(item)
        return result
    
    def clear(self):
        self._heap.clear()
    
    def to_list(self) -> List[Tuple[float, Any]]:
        return [(item.priority, item.value) for item in self._heap]


class MaxHeap:
    
    def __init__(self):
        self._min_heap = MinHeap()
    
    def __len__(self) -> int:
        return len(self._min_heap)
    
    def __bool__(self) -> bool:
        return bool(self._min_heap)
    
    def push(self, priority: float, value: Any = None):
        self._min_heap.push(-priority, value if value is not None else priority)
    
    def pop(self) -> Optional[Tuple[float, Any]]:
        result = self._min_heap.pop()
        if result:
            return (-result[0], result[1])
        return None
    
    def peek(self) -> Optional[Tuple[float, Any]]:
        result = self._min_heap.peek()
        if result:
            return (-result[0], result[1])
        return None
    
    def push_pop(self, priority: float, value: Any = None) -> Tuple[float, Any]:
        result = self._min_heap.push_pop(-priority, value if value is not None else priority)
        return (-result[0], result[1])
    
    def heapify(self, items: List[Tuple[float, Any]]):
        negated = [(-p, v) for p, v in items]
        self._min_heap.heapify(negated)
    
    def get_top_n(self, n: int) -> List[Tuple[float, Any]]:
        result = self._min_heap.get_top_n(n)
        return [(-p, v) for p, v in result]
    
    def clear(self):
        self._min_heap.clear()
    
    def to_list(self) -> List[Tuple[float, Any]]:
        return [(-item.priority, item.value) for item in self._min_heap._heap]


class PriorityQueue:
    
    def __init__(self, min_queue: bool = True):
        self._heap = MinHeap() if min_queue else MaxHeap()
        self._entry_finder = {}
        self._counter = 0
        self._REMOVED = object()
    
    def __len__(self) -> int:
        return len(self._entry_finder)
    
    def __bool__(self) -> bool:
        return len(self._entry_finder) > 0
    
    def __contains__(self, value: Any) -> bool:
        return value in self._entry_finder
    
    def add(self, value: Any, priority: float):
        if value in self._entry_finder:
            self.remove(value)
        
        entry = [priority, self._counter, value]
        self._entry_finder[value] = entry
        self._heap.push(priority, entry)
        self._counter += 1
    
    def remove(self, value: Any) -> bool:
        entry = self._entry_finder.pop(value, None)
        if entry:
            entry[-1] = self._REMOVED
            return True
        return False
    
    def pop(self) -> Optional[Tuple[float, Any]]:
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
        while self._heap:
            result = self._heap.peek()
            if result:
                priority, entry = result
                if isinstance(entry, list) and entry[-1] is not self._REMOVED:
                    return (priority, entry[-1])
                self._heap.pop()
        return None
    
    def update_priority(self, value: Any, new_priority: float):
        self.add(value, new_priority)
    
    def get_priority(self, value: Any) -> Optional[float]:
        entry = self._entry_finder.get(value)
        if entry and entry[-1] is not self._REMOVED:
            return entry[0]
        return None


