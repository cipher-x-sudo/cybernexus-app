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
        new_node = ListNode(data=data)
        
        if not self._tail:
            self._head = self._tail = new_node
        else:
            new_node.prev = self._tail
            self._tail.next = new_node
            self._tail = new_node
        
        self._size += 1
    
    def prepend(self, data: Any):
        new_node = ListNode(data=data)
        
        if not self._head:
            self._head = self._tail = new_node
        else:
            new_node.next = self._head
            self._head.prev = new_node
            self._head = new_node
        
        self._size += 1
    
    def insert(self, index: int, data: Any):
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
        new_node = ListNode(data=data, prev=node, next=node.next)
        
        if node.next:
            node.next.prev = new_node
        else:
            self._tail = new_node
        
        node.next = new_node
        self._size += 1
        return new_node
    
    def insert_before(self, node: ListNode, data: Any) -> ListNode:
        new_node = ListNode(data=data, prev=node.prev, next=node)
        
        if node.prev:
            node.prev.next = new_node
        else:
            self._head = new_node
        
        node.prev = new_node
        self._size += 1
        return new_node
    
    def pop_front(self) -> Optional[Any]:
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
        node = self._head
        
        while node:
            if node.data == data:
                self._remove_node(node)
                return True
            node = node.next
        
        return False
    
    def remove_at(self, index: int) -> Optional[Any]:
        node = self._get_node(index)
        if node is None:
            return None
        
        data = node.data
        self._remove_node(node)
        return data
    
    def _remove_node(self, node: ListNode):
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
        node = self._head
        
        while node:
            if node.data == data:
                return node
            node = node.next
        
        return None
    
    def find_by(self, predicate: Callable[[Any], bool]) -> Optional[ListNode]:
        node = self._head
        
        while node:
            if predicate(node.data):
                return node
            node = node.next
        
        return None
    
    def index_of(self, data: Any) -> int:
        node = self._head
        index = 0
        
        while node:
            if node.data == data:
                return index
            node = node.next
            index += 1
        
        return -1
    
    def contains(self, data: Any) -> bool:
        return self.find(data) is not None
    
    def forward(self) -> Generator[Any, None, None]:
        node = self._head
        while node:
            yield node.data
            node = node.next
    
    def backward(self) -> Generator[Any, None, None]:
        node = self._tail
        while node:
            yield node.data
            node = node.prev
    
    def nodes_forward(self) -> Generator[ListNode, None, None]:
        node = self._head
        while node:
            yield node
            node = node.next
    
    def nodes_backward(self) -> Generator[ListNode, None, None]:
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
        self._head = None
        self._tail = None
        self._size = 0
    
    def reverse(self):
        current = self._head
        
        while current:
            current.prev, current.next = current.next, current.prev
            current = current.prev
        
        self._head, self._tail = self._tail, self._head
    
    def to_list(self) -> list:
        return list(self.forward())
    
    @classmethod
    def from_list(cls, items: list) -> "DoublyLinkedList":
        dll = cls()
        for item in items:
            dll.append(item)
        return dll
    
    def copy(self) -> "DoublyLinkedList":
        return DoublyLinkedList.from_list(self.to_list())
    
    def filter(self, predicate: Callable[[Any], bool]) -> "DoublyLinkedList":
        result = DoublyLinkedList()
        for data in self:
            if predicate(data):
                result.append(data)
        return result
    
    def map(self, func: Callable[[Any], Any]) -> "DoublyLinkedList":
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
        new_node = SinglyLinkedList.Node(data=data)
        
        if not self._tail:
            self._head = self._tail = new_node
        else:
            self._tail.next = new_node
            self._tail = new_node
        
        self._size += 1
    
    def prepend(self, data: Any):
        new_node = SinglyLinkedList.Node(data=data, next=self._head)
        self._head = new_node
        
        if not self._tail:
            self._tail = new_node
        
        self._size += 1
    
    def pop_front(self) -> Optional[Any]:
        if not self._head:
            return None
        
        data = self._head.data
        self._head = self._head.next
        
        if not self._head:
            self._tail = None
        
        self._size -= 1
        return data
    
    def to_list(self) -> list:
        return list(self)


