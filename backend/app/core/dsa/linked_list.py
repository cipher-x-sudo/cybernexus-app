"""Doubly Linked List implementation.

This module implements a doubly linked list with bidirectional traversal.
Provides O(1) insertion and deletion at both ends, making it suitable for
timeline event storage and LRU cache implementation.

DSA Concept: Doubly Linked List
- Bidirectional traversal support
- O(1) insertion/deletion at head and tail
- O(n) search operation
- Iterator support for forward and backward iteration
- Ideal for timeline event storage and LRU cache
"""

from typing import Any, Optional, Generator, Callable
from dataclasses import dataclass


@dataclass
class ListNode:
    data: Any
    prev: Optional["ListNode"] = None
    next: Optional["ListNode"] = None


class DoublyLinkedList:
    
    def __init__(self):
        self._head: Optional[ListNode] = None
        self._tail: Optional[ListNode] = None
        self._size = 0
    
    def __len__(self) -> int:
        return self._size
    
    def __bool__(self) -> bool:
        return self._size > 0
    
    def __iter__(self) -> Generator[Any, None, None]:
        yield from self.forward()
    
    def __reversed__(self) -> Generator[Any, None, None]:
        yield from self.backward()
    
    def __getitem__(self, index: int) -> Any:
        node = self._get_node(index)
        if node is None:
            raise IndexError("Index out of range")
        return node.data
    
    def __setitem__(self, index: int, value: Any):
        node = self._get_node(index)
        if node is None:
            raise IndexError("Index out of range")
        node.data = value
    
    def _get_node(self, index: int) -> Optional[ListNode]:
        """Get the node at a specific index using optimized traversal.
        
        Args:
            index: Index of the node to retrieve
        
        Returns:
            ListNode at the index, or None if index is out of range
        """
        if index < 0:
            index += self._size
        
        if index < 0 or index >= self._size:
            return None
        
        if index < self._size // 2:
            node = self._head
            for _ in range(index):
                node = node.next
        else:
            node = self._tail
            for _ in range(self._size - 1 - index):
                node = node.prev
        
        return node
    
    def append(self, data: Any):
        """Add an element to the end of the list.
        
        Args:
            data: Data to append
        """
        new_node = ListNode(data=data)
        
        if not self._tail:
            self._head = self._tail = new_node
        else:
            new_node.prev = self._tail
            self._tail.next = new_node
            self._tail = new_node
        
        self._size += 1
    
    def prepend(self, data: Any):
        """Add an element to the beginning of the list.
        
        Args:
            data: Data to prepend
        """
        new_node = ListNode(data=data)
        
        if not self._head:
            self._head = self._tail = new_node
        else:
            new_node.next = self._head
            self._head.prev = new_node
            self._head = new_node
        
        self._size += 1
    
    def insert(self, index: int, data: Any):
        """Insert an element at a specific index.
        
        Args:
            index: Index to insert at
            data: Data to insert
        """
        if index < 0:
            index += self._size + 1
        
        if index <= 0:
            self.prepend(data)
            return
        
        if index >= self._size:
            self.append(data)
            return
        
        current = self._get_node(index)
        if current is None:
            self.append(data)
            return
        
        new_node = ListNode(data=data, prev=current.prev, next=current)
        current.prev.next = new_node
        current.prev = new_node
        self._size += 1
    
    def insert_after(self, node: ListNode, data: Any) -> ListNode:
        """Insert an element after a specific node.
        
        Args:
            node: Node to insert after
            data: Data to insert
        
        Returns:
            The newly created node
        """
        new_node = ListNode(data=data, prev=node, next=node.next)
        
        if node.next:
            node.next.prev = new_node
        else:
            self._tail = new_node
        
        node.next = new_node
        self._size += 1
        return new_node
    
    def insert_before(self, node: ListNode, data: Any) -> ListNode:
        """Insert an element before a specific node.
        
        Args:
            node: Node to insert before
            data: Data to insert
        
        Returns:
            The newly created node
        """
        new_node = ListNode(data=data, prev=node.prev, next=node)
        
        if node.prev:
            node.prev.next = new_node
        else:
            self._head = new_node
        
        node.prev = new_node
        self._size += 1
        return new_node
    
    def pop_front(self) -> Optional[Any]:
        """Remove and return the first element.
        
        Returns:
            Data from the first element, or None if list is empty
        """
        if not self._head:
            return None
        
        data = self._head.data
        self._head = self._head.next
        
        if self._head:
            self._head.prev = None
        else:
            self._tail = None
        
        self._size -= 1
        return data
    
    def pop_back(self) -> Optional[Any]:
        """Remove and return the last element.
        
        Returns:
            Data from the last element, or None if list is empty
        """
        if not self._tail:
            return None
        
        data = self._tail.data
        self._tail = self._tail.prev
        
        if self._tail:
            self._tail.next = None
        else:
            self._head = None
        
        self._size -= 1
        return data
    
    def remove(self, data: Any) -> bool:
        """Remove the first occurrence of an element.
        
        Args:
            data: Data to remove
        
        Returns:
            True if element was found and removed, False otherwise
        """
        node = self._head
        
        while node:
            if node.data == data:
                self._remove_node(node)
                return True
            node = node.next
        
        return False
    
    def remove_at(self, index: int) -> Optional[Any]:
        """Remove and return the element at a specific index.
        
        Args:
            index: Index of element to remove
        
        Returns:
            Data from the removed element, or None if index is out of range
        """
        node = self._get_node(index)
        if node is None:
            return None
        
        data = node.data
        self._remove_node(node)
        return data
    
    def _remove_node(self, node: ListNode):
        """Remove a specific node from the list.
        
        Args:
            node: Node to remove
        """
        if node.prev:
            node.prev.next = node.next
        else:
            self._head = node.next
        
        if node.next:
            node.next.prev = node.prev
        else:
            self._tail = node.prev
        
        self._size -= 1
    
    def find(self, data: Any) -> Optional[ListNode]:
        """Find the first node containing the specified data.
        
        Args:
            data: Data to search for
        
        Returns:
            ListNode if found, None otherwise
        """
        node = self._head
        
        while node:
            if node.data == data:
                return node
            node = node.next
        
        return None
    
    def find_by(self, predicate: Callable[[Any], bool]) -> Optional[ListNode]:
        """Find the first node matching a predicate function.
        
        Args:
            predicate: Function that takes data and returns bool
        
        Returns:
            ListNode if found, None otherwise
        """
        node = self._head
        
        while node:
            if predicate(node.data):
                return node
            node = node.next
        
        return None
    
    def index_of(self, data: Any) -> int:
        """Get the index of the first occurrence of an element.
        
        Args:
            data: Data to search for
        
        Returns:
            Index of the element, or -1 if not found
        """
        node = self._head
        index = 0
        
        while node:
            if node.data == data:
                return index
            node = node.next
            index += 1
        
        return -1
    
    def contains(self, data: Any) -> bool:
        """Check if the list contains an element.
        
        Args:
            data: Data to check for
        
        Returns:
            True if element exists, False otherwise
        """
        return self.find(data) is not None
    
    def forward(self) -> Generator[Any, None, None]:
        """Generate elements in forward order.
        
        Yields:
            Elements from head to tail
        """
        node = self._head
        while node:
            yield node.data
            node = node.next
    
    def backward(self) -> Generator[Any, None, None]:
        """Generate elements in backward order.
        
        Yields:
            Elements from tail to head
        """
        node = self._tail
        while node:
            yield node.data
            node = node.prev
    
    def nodes_forward(self) -> Generator[ListNode, None, None]:
        """Generate nodes in forward order.
        
        Yields:
            ListNode instances from head to tail
        """
        node = self._head
        while node:
            yield node
            node = node.next
    
    def nodes_backward(self) -> Generator[ListNode, None, None]:
        """Generate nodes in backward order.
        
        Yields:
            ListNode instances from tail to head
        """
        node = self._tail
        while node:
            yield node
            node = node.prev
    
    @property
    def head(self) -> Optional[Any]:
        return self._head.data if self._head else None
    
    @property
    def tail(self) -> Optional[Any]:
        return self._tail.data if self._tail else None
    
    @property
    def head_node(self) -> Optional[ListNode]:
        return self._head
    
    @property
    def tail_node(self) -> Optional[ListNode]:
        return self._tail
    
    def clear(self):
        """Remove all elements from the list."""
        self._head = None
        self._tail = None
        self._size = 0
    
    def reverse(self):
        """Reverse the list in-place."""
        current = self._head
        
        while current:
            current.prev, current.next = current.next, current.prev
            current = current.prev
        
        self._head, self._tail = self._tail, self._head
    
    def to_list(self) -> list:
        """Convert the linked list to a Python list.
        
        Returns:
            List containing all elements in forward order
        """
        return list(self.forward())
    
    @classmethod
    def from_list(cls, items: list) -> "DoublyLinkedList":
        """Create a DoublyLinkedList from a list.
        
        Args:
            items: List of items to add
        
        Returns:
            New DoublyLinkedList instance
        """
        dll = cls()
        for item in items:
            dll.append(item)
        return dll
    
    def copy(self) -> "DoublyLinkedList":
        """Create a shallow copy of the list.
        
        Returns:
            New DoublyLinkedList instance with copied elements
        """
        return DoublyLinkedList.from_list(self.to_list())
    
    def filter(self, predicate: Callable[[Any], bool]) -> "DoublyLinkedList":
        """Create a new list with elements matching a predicate.
        
        Args:
            predicate: Function that takes data and returns bool
        
        Returns:
            New DoublyLinkedList with filtered elements
        """
        result = DoublyLinkedList()
        for data in self:
            if predicate(data):
                result.append(data)
        return result
    
    def map(self, func: Callable[[Any], Any]) -> "DoublyLinkedList":
        """Create a new list with elements transformed by a function.
        
        Args:
            func: Function to apply to each element
        
        Returns:
            New DoublyLinkedList with transformed elements
        """
        result = DoublyLinkedList()
        for data in self:
            result.append(func(data))
        return result


class SinglyLinkedList:
    
    @dataclass
    class Node:
        data: Any
        next: Optional["SinglyLinkedList.Node"] = None
    
    def __init__(self):
        self._head: Optional[SinglyLinkedList.Node] = None
        self._tail: Optional[SinglyLinkedList.Node] = None
        self._size = 0
    
    def __len__(self) -> int:
        return self._size
    
    def __iter__(self) -> Generator[Any, None, None]:
        node = self._head
        while node:
            yield node.data
            node = node.next
    
    def append(self, data: Any):
        """Add an element to the end of the list.
        
        Args:
            data: Data to append
        """
        new_node = SinglyLinkedList.Node(data=data)
        
        if not self._tail:
            self._head = self._tail = new_node
        else:
            self._tail.next = new_node
            self._tail = new_node
        
        self._size += 1
    
    def prepend(self, data: Any):
        """Add an element to the beginning of the list.
        
        Args:
            data: Data to prepend
        """
        new_node = SinglyLinkedList.Node(data=data, next=self._head)
        self._head = new_node
        
        if not self._tail:
            self._tail = new_node
        
        self._size += 1
    
    def pop_front(self) -> Optional[Any]:
        """Remove and return the first element.
        
        Returns:
            Data from the first element, or None if list is empty
        """
        if not self._head:
            return None
        
        data = self._head.data
        self._head = self._head.next
        
        if not self._head:
            self._tail = None
        
        self._size -= 1
        return data
    
    def to_list(self) -> list:
        """Convert the linked list to a Python list.
        
        Returns:
            List containing all elements
        """
        return list(self)


