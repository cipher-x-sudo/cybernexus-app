"""
Tests for Heap DSA Implementation
"""

import pytest
from app.core.dsa.heap import MinHeap, MaxHeap, PriorityQueue


class TestMinHeap:
    """Test suite for MinHeap data structure."""
    
    def test_create_empty_heap(self):
        """Test creating an empty heap."""
        h = MinHeap()
        assert len(h) == 0
        assert not h
    
    def test_push_single(self):
        """Test pushing a single element."""
        h = MinHeap()
        h.push(5, "five")
        
        assert len(h) == 1
        assert h
    
    def test_push_multiple(self):
        """Test pushing multiple elements."""
        h = MinHeap()
        h.push(5, "five")
        h.push(3, "three")
        h.push(7, "seven")
        
        assert len(h) == 3
    
    def test_peek(self):
        """Test peeking at minimum."""
        h = MinHeap()
        h.push(5, "five")
        h.push(3, "three")
        h.push(7, "seven")
        
        result = h.peek()
        
        assert result == (3, "three")
        assert len(h) == 3  # Peek doesn't remove
    
    def test_pop(self):
        """Test popping minimum."""
        h = MinHeap()
        h.push(5, "five")
        h.push(3, "three")
        h.push(7, "seven")
        
        result = h.pop()
        
        assert result == (3, "three")
        assert len(h) == 2
    
    def test_pop_order(self):
        """Test that pop returns elements in order."""
        h = MinHeap()
        h.push(5, "five")
        h.push(3, "three")
        h.push(7, "seven")
        h.push(1, "one")
        h.push(9, "nine")
        
        results = []
        while h:
            results.append(h.pop()[0])
        
        assert results == [1, 3, 5, 7, 9]
    
    def test_pop_empty(self):
        """Test popping from empty heap."""
        h = MinHeap()
        
        assert h.pop() is None
    
    def test_peek_empty(self):
        """Test peeking empty heap."""
        h = MinHeap()
        
        assert h.peek() is None
    
    def test_push_pop(self):
        """Test push_pop operation."""
        h = MinHeap()
        h.push(5, "five")
        h.push(3, "three")
        
        # Push 1, should become new min, return it
        result = h.push_pop(1, "one")
        assert result == (1, "one")
        
        # Push 7, should return 3 (current min)
        result = h.push_pop(7, "seven")
        assert result == (3, "three")
    
    def test_replace(self):
        """Test replace operation."""
        h = MinHeap()
        h.push(5, "five")
        h.push(3, "three")
        
        result = h.replace(10, "ten")
        
        assert result == (3, "three")
        assert h.peek()[0] == 5
    
    def test_heapify(self):
        """Test building heap from list."""
        h = MinHeap()
        items = [(5, "five"), (3, "three"), (7, "seven"), (1, "one")]
        
        h.heapify(items)
        
        assert len(h) == 4
        assert h.peek() == (1, "one")
    
    def test_get_top_n(self):
        """Test getting top N elements."""
        h = MinHeap()
        for i in [5, 3, 7, 1, 9, 2, 8]:
            h.push(i, f"value_{i}")
        
        top3 = h.get_top_n(3)
        
        assert len(top3) == 3
        priorities = [p for p, v in top3]
        assert priorities == [1, 2, 3]
    
    def test_clear(self):
        """Test clearing heap."""
        h = MinHeap()
        h.push(5, "five")
        h.push(3, "three")
        
        h.clear()
        
        assert len(h) == 0
    
    def test_to_list(self):
        """Test converting to list."""
        h = MinHeap()
        h.push(5, "five")
        h.push(3, "three")
        
        items = h.to_list()
        
        assert len(items) == 2


class TestMaxHeap:
    """Test suite for MaxHeap data structure."""
    
    def test_create_empty_heap(self):
        """Test creating an empty heap."""
        h = MaxHeap()
        assert len(h) == 0
    
    def test_push_and_peek(self):
        """Test pushing and peeking."""
        h = MaxHeap()
        h.push(5, "five")
        h.push(3, "three")
        h.push(7, "seven")
        
        result = h.peek()
        
        assert result == (7, "seven")
    
    def test_pop_order(self):
        """Test that pop returns elements in descending order."""
        h = MaxHeap()
        h.push(5, "five")
        h.push(3, "three")
        h.push(7, "seven")
        h.push(1, "one")
        h.push(9, "nine")
        
        results = []
        while h:
            results.append(h.pop()[0])
        
        assert results == [9, 7, 5, 3, 1]
    
    def test_heapify(self):
        """Test building max heap from list."""
        h = MaxHeap()
        items = [(5, "five"), (3, "three"), (7, "seven"), (1, "one")]
        
        h.heapify(items)
        
        assert len(h) == 4
        assert h.peek() == (7, "seven")
    
    def test_get_top_n(self):
        """Test getting top N elements (largest)."""
        h = MaxHeap()
        for i in [5, 3, 7, 1, 9, 2, 8]:
            h.push(i, f"value_{i}")
        
        top3 = h.get_top_n(3)
        
        assert len(top3) == 3
        priorities = [p for p, v in top3]
        assert priorities == [9, 8, 7]


class TestPriorityQueue:
    """Test suite for PriorityQueue with update capability."""
    
    def test_create_empty_queue(self):
        """Test creating an empty queue."""
        pq = PriorityQueue()
        assert len(pq) == 0
    
    def test_add_and_pop(self):
        """Test adding and popping items."""
        pq = PriorityQueue()
        pq.add("item1", 5)
        pq.add("item2", 3)
        pq.add("item3", 7)
        
        result = pq.pop()
        
        assert result == (3, "item2")  # Min queue by default
    
    def test_update_priority(self):
        """Test updating priority of existing item."""
        pq = PriorityQueue()
        pq.add("item1", 5)
        pq.add("item2", 3)
        
        pq.update_priority("item1", 1)
        
        result = pq.pop()
        assert result == (1, "item1")
    
    def test_remove(self):
        """Test removing item from queue."""
        pq = PriorityQueue()
        pq.add("item1", 5)
        pq.add("item2", 3)
        
        assert pq.remove("item1")
        assert len(pq) == 1
    
    def test_contains(self):
        """Test checking if item in queue."""
        pq = PriorityQueue()
        pq.add("item1", 5)
        
        assert "item1" in pq
        assert "item2" not in pq
    
    def test_get_priority(self):
        """Test getting priority of item."""
        pq = PriorityQueue()
        pq.add("item1", 5)
        
        assert pq.get_priority("item1") == 5
        assert pq.get_priority("missing") is None
    
    def test_max_queue(self):
        """Test max priority queue."""
        pq = PriorityQueue(min_queue=False)
        pq.add("item1", 5)
        pq.add("item2", 3)
        pq.add("item3", 7)
        
        result = pq.pop()
        
        assert result == (7, "item3")  # Max comes first


