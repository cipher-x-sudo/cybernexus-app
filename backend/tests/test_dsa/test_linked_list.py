"""
Tests for Linked List DSA Implementation
"""

import pytest
from app.core.dsa.linked_list import DoublyLinkedList, SinglyLinkedList


class TestDoublyLinkedList:
    """Test suite for Doubly Linked List data structure."""
    
    def test_create_empty_list(self):
        """Test creating an empty list."""
        dll = DoublyLinkedList()
        assert len(dll) == 0
        assert not dll
    
    def test_append(self):
        """Test appending elements."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        assert len(dll) == 3
        assert dll.head == 1
        assert dll.tail == 3
    
    def test_prepend(self):
        """Test prepending elements."""
        dll = DoublyLinkedList()
        dll.prepend(1)
        dll.prepend(2)
        dll.prepend(3)
        
        assert len(dll) == 3
        assert dll.head == 3
        assert dll.tail == 1
    
    def test_insert(self):
        """Test inserting at index."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(3)
        dll.insert(1, 2)  # Insert 2 at index 1
        
        assert dll.to_list() == [1, 2, 3]
    
    def test_pop_front(self):
        """Test removing from front."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        result = dll.pop_front()
        
        assert result == 1
        assert len(dll) == 2
        assert dll.head == 2
    
    def test_pop_back(self):
        """Test removing from back."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        result = dll.pop_back()
        
        assert result == 3
        assert len(dll) == 2
        assert dll.tail == 2
    
    def test_pop_empty(self):
        """Test popping from empty list."""
        dll = DoublyLinkedList()
        
        assert dll.pop_front() is None
        assert dll.pop_back() is None
    
    def test_remove(self):
        """Test removing by value."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        assert dll.remove(2)
        assert dll.to_list() == [1, 3]
    
    def test_remove_missing(self):
        """Test removing non-existent value."""
        dll = DoublyLinkedList()
        dll.append(1)
        
        assert not dll.remove(5)
    
    def test_remove_at(self):
        """Test removing at index."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        result = dll.remove_at(1)
        
        assert result == 2
        assert dll.to_list() == [1, 3]
    
    def test_find(self):
        """Test finding node by value."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        node = dll.find(2)
        
        assert node is not None
        assert node.data == 2
    
    def test_find_missing(self):
        """Test finding non-existent value."""
        dll = DoublyLinkedList()
        dll.append(1)
        
        assert dll.find(5) is None
    
    def test_index_of(self):
        """Test getting index of value."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        assert dll.index_of(2) == 1
        assert dll.index_of(5) == -1
    
    def test_contains(self):
        """Test checking if value exists."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        
        assert dll.contains(1)
        assert not dll.contains(5)
    
    def test_getitem(self):
        """Test bracket access."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        assert dll[0] == 1
        assert dll[1] == 2
        assert dll[-1] == 3  # Negative index
    
    def test_setitem(self):
        """Test bracket assignment."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        
        dll[1] = 10
        
        assert dll[1] == 10
    
    def test_forward_iteration(self):
        """Test forward iteration."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        result = list(dll.forward())
        
        assert result == [1, 2, 3]
    
    def test_backward_iteration(self):
        """Test backward iteration."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        result = list(dll.backward())
        
        assert result == [3, 2, 1]
    
    def test_iter(self):
        """Test __iter__."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        
        result = list(dll)
        
        assert result == [1, 2]
    
    def test_reversed(self):
        """Test __reversed__."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        result = list(reversed(dll))
        
        assert result == [3, 2, 1]
    
    def test_reverse_in_place(self):
        """Test reversing list in place."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        dll.reverse()
        
        assert dll.to_list() == [3, 2, 1]
    
    def test_clear(self):
        """Test clearing list."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        
        dll.clear()
        
        assert len(dll) == 0
        assert dll.head is None
        assert dll.tail is None
    
    def test_to_list(self):
        """Test converting to Python list."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        dll.append(3)
        
        result = dll.to_list()
        
        assert result == [1, 2, 3]
    
    def test_from_list(self):
        """Test creating from Python list."""
        dll = DoublyLinkedList.from_list([1, 2, 3])
        
        assert len(dll) == 3
        assert dll.to_list() == [1, 2, 3]
    
    def test_copy(self):
        """Test creating a copy."""
        dll = DoublyLinkedList()
        dll.append(1)
        dll.append(2)
        
        copy = dll.copy()
        
        assert copy.to_list() == dll.to_list()
        assert copy is not dll
    
    def test_filter(self):
        """Test filtering list."""
        dll = DoublyLinkedList.from_list([1, 2, 3, 4, 5])
        
        evens = dll.filter(lambda x: x % 2 == 0)
        
        assert evens.to_list() == [2, 4]
    
    def test_map(self):
        """Test mapping over list."""
        dll = DoublyLinkedList.from_list([1, 2, 3])
        
        doubled = dll.map(lambda x: x * 2)
        
        assert doubled.to_list() == [2, 4, 6]


class TestSinglyLinkedList:
    """Test suite for Singly Linked List."""
    
    def test_create_empty(self):
        """Test creating empty list."""
        sll = SinglyLinkedList()
        assert len(sll) == 0
    
    def test_append(self):
        """Test appending."""
        sll = SinglyLinkedList()
        sll.append(1)
        sll.append(2)
        
        assert sll.to_list() == [1, 2]
    
    def test_prepend(self):
        """Test prepending."""
        sll = SinglyLinkedList()
        sll.prepend(1)
        sll.prepend(2)
        
        assert sll.to_list() == [2, 1]
    
    def test_pop_front(self):
        """Test popping from front."""
        sll = SinglyLinkedList()
        sll.append(1)
        sll.append(2)
        
        result = sll.pop_front()
        
        assert result == 1
        assert len(sll) == 1


