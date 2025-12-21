from typing import Any, Optional, List, Tuple, Generator, Callable
from dataclasses import dataclass


@dataclass
class HashNode:
    key: Any
    value: Any
    next: Optional["HashNode"] = None


class HashMap:
    
    DEFAULT_CAPACITY = 16
    LOAD_FACTOR_THRESHOLD = 0.75
    
    def __init__(self, capacity: int = None):
        self._capacity = capacity or self.DEFAULT_CAPACITY
        self._buckets: List[Optional[HashNode]] = [None] * self._capacity
        self._size = 0
    
    def __len__(self) -> int:
        return self._size
    
    def __contains__(self, key: Any) -> bool:
        return self.get(key) is not None
    
    def __getitem__(self, key: Any) -> Any:
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value
    
    def __setitem__(self, key: Any, value: Any):
        self.put(key, value)
    
    def __delitem__(self, key: Any):
        if not self.remove(key):
            raise KeyError(key)
    
    def __iter__(self) -> Generator[Any, None, None]:
        yield from self.keys()
    
    def _hash(self, key: Any) -> int:
        return hash(key) % self._capacity
    
    def _resize(self):
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = [None] * self._capacity
        self._size = 0
        
        for bucket in old_buckets:
            node = bucket
            while node:
                self.put(node.key, node.value)
                node = node.next
    
    def put(self, key: Any, value: Any) -> bool:
        if self._size / self._capacity >= self.LOAD_FACTOR_THRESHOLD:
            self._resize()
        
        index = self._hash(key)
        node = self._buckets[index]
        
        while node:
            if node.key == key:
                node.value = value
                return False
            node = node.next
        
        new_node = HashNode(key=key, value=value, next=self._buckets[index])
        self._buckets[index] = new_node
        self._size += 1
        return True
    
    def get(self, key: Any, default: Any = None) -> Any:
        index = self._hash(key)
        node = self._buckets[index]
        
        while node:
            if node.key == key:
                return node.value
            node = node.next
        
        return default
    
    def remove(self, key: Any) -> bool:
        index = self._hash(key)
        node = self._buckets[index]
        prev = None
        
        while node:
            if node.key == key:
                if prev:
                    prev.next = node.next
                else:
                    self._buckets[index] = node.next
                self._size -= 1
                return True
            prev = node
            node = node.next
        
        return False
    
    def keys(self) -> Generator[Any, None, None]:
        for bucket in self._buckets:
            node = bucket
            while node:
                yield node.key
                node = node.next
    
    def values(self) -> Generator[Any, None, None]:
        for bucket in self._buckets:
            node = bucket
            while node:
                yield node.value
                node = node.next
    
    def items(self) -> Generator[Tuple[Any, Any], None, None]:
        for bucket in self._buckets:
            node = bucket
            while node:
                yield (node.key, node.value)
                node = node.next
    
    def clear(self):
        self._buckets = [None] * self._capacity
        self._size = 0
    
    def update(self, other: dict = None, **kwargs):
        if other:
            for key, value in other.items():
                self.put(key, value)
        for key, value in kwargs.items():
            self.put(key, value)
    
    def setdefault(self, key: Any, default: Any = None) -> Any:
        value = self.get(key)
        if value is None:
            self.put(key, default)
            return default
        return value
    
    def pop(self, key: Any, default: Any = None) -> Any:
        value = self.get(key)
        if value is not None:
            self.remove(key)
            return value
        return default
    
    def load_factor(self) -> float:
        return self._size / self._capacity
    
    def bucket_distribution(self) -> List[int]:
        distribution = []
        for bucket in self._buckets:
            count = 0
            node = bucket
            while node:
                count += 1
                node = node.next
            distribution.append(count)
        return distribution
    
    def stats(self) -> dict:
        distribution = self.bucket_distribution()
        non_empty = [d for d in distribution if d > 0]
        
        return {
            "size": self._size,
            "capacity": self._capacity,
            "load_factor": self.load_factor(),
            "empty_buckets": distribution.count(0),
            "max_chain_length": max(distribution) if distribution else 0,
            "avg_chain_length": sum(non_empty) / len(non_empty) if non_empty else 0
        }
    
    def to_dict(self) -> dict:
        return dict(self.items())
    
    @classmethod
    def from_dict(cls, d: dict) -> "HashMap":
        hashmap = cls()
        for key, value in d.items():
            hashmap.put(key, value)
        return hashmap


class HashSet:
    
    def __init__(self):
        self._map = HashMap()
    
    def __len__(self) -> int:
        return len(self._map)
    
    def __contains__(self, item: Any) -> bool:
        return item in self._map
    
    def __iter__(self) -> Generator[Any, None, None]:
        yield from self._map.keys()
    
    def add(self, item: Any) -> bool:
        return self._map.put(item, True)
    
    def remove(self, item: Any) -> bool:
        return self._map.remove(item)
    
    def discard(self, item: Any):
        self._map.remove(item)
    
    def clear(self):
        self._map.clear()
    
    def union(self, other: "HashSet") -> "HashSet":
        result = HashSet()
        for item in self:
            result.add(item)
        for item in other:
            result.add(item)
        return result
    
    def intersection(self, other: "HashSet") -> "HashSet":
        result = HashSet()
        for item in self:
            if item in other:
                result.add(item)
        return result
    
    def difference(self, other: "HashSet") -> "HashSet":
        result = HashSet()
        for item in self:
            if item not in other:
                result.add(item)
        return result
    
    def to_list(self) -> List[Any]:
        return list(self)
    
    @classmethod
    def from_list(cls, items: List[Any]) -> "HashSet":
        s = cls()
        for item in items:
            s.add(item)
        return s


