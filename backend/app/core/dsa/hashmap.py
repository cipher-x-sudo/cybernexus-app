"""HashMap (Separate Chaining) implementation.

This module implements a hash map using separate chaining for collision resolution.
Automatically resizes when load factor exceeds threshold to maintain O(1) average
time complexity for insert, search, and delete operations.

DSA Concept: HashMap (Separate Chaining)
- Automatic resizing based on load factor
- Collision handling with linked list chaining
- O(1) average time complexity for all operations
- O(n) worst-case time complexity
"""

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
        """Insert or update a key-value pair.
        
        DSA-USED:
        - HashMap: Separate chaining hash map insertion with automatic resizing
        
        Args:
            key: Key to insert
            value: Value to associate with key
        
        Returns:
            True if new key was inserted, False if existing key was updated
        """
        if self._size / self._capacity >= self.LOAD_FACTOR_THRESHOLD:
            self._resize()  # DSA-USED: HashMap
        
        index = self._hash(key)  # DSA-USED: HashMap
        node = self._buckets[index]  # DSA-USED: HashMap
        
        while node:  # DSA-USED: HashMap
            if node.key == key:
                node.value = value
                return False
            node = node.next
        
        new_node = HashNode(key=key, value=value, next=self._buckets[index])
        self._buckets[index] = new_node  # DSA-USED: HashMap
        self._size += 1
        return True
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Retrieve value by key.
        
        DSA-USED:
        - HashMap: O(1) average case lookup using hash function and chaining
        
        Args:
            key: Key to look up
            default: Default value if key not found
        
        Returns:
            Value associated with key, or default if not found
        """
        index = self._hash(key)  # DSA-USED: HashMap
        node = self._buckets[index]  # DSA-USED: HashMap
        
        while node:  # DSA-USED: HashMap
            if node.key == key:
                return node.value
            node = node.next
        
        return default
    
    def remove(self, key: Any) -> bool:
        """Remove a key-value pair from the map.
        
        DSA-USED:
        - HashMap: O(1) average case deletion using hash function and chaining
        
        Args:
            key: Key to remove
        
        Returns:
            True if key was found and removed, False otherwise
        """
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
        """Generate all keys in the map.
        
        Yields:
            All keys in the map
        """
        for bucket in self._buckets:
            node = bucket
            while node:
                yield node.key
                node = node.next
    
    def values(self) -> Generator[Any, None, None]:
        """Generate all values in the map.
        
        Yields:
            All values in the map
        """
        for bucket in self._buckets:
            node = bucket
            while node:
                yield node.value
                node = node.next
    
    def items(self) -> Generator[Tuple[Any, Any], None, None]:
        """Generate all key-value pairs in the map.
        
        Yields:
            Tuples of (key, value) pairs
        """
        for bucket in self._buckets:
            node = bucket
            while node:
                yield (node.key, node.value)
                node = node.next
    
    def clear(self):
        """Remove all key-value pairs from the map."""
        self._buckets = [None] * self._capacity
        self._size = 0
    
    def update(self, other: dict = None, **kwargs):
        """Update the map with key-value pairs from another dict or keyword arguments.
        
        Args:
            other: Dictionary to update from
            **kwargs: Additional key-value pairs to add
        """
        if other:
            for key, value in other.items():
                self.put(key, value)
        for key, value in kwargs.items():
            self.put(key, value)
    
    def setdefault(self, key: Any, default: Any = None) -> Any:
        """Get value for key, or set to default if key doesn't exist.
        
        Args:
            key: Key to look up
            default: Default value to set if key not found
        
        Returns:
            Value associated with key, or default if key was not present
        """
        value = self.get(key)
        if value is None:
            self.put(key, default)
            return default
        return value
    
    def pop(self, key: Any, default: Any = None) -> Any:
        """Remove and return value for key, or return default if key not found.
        
        Args:
            key: Key to remove
            default: Default value to return if key not found
        
        Returns:
            Value associated with key, or default if key was not present
        """
        value = self.get(key)
        if value is not None:
            self.remove(key)
            return value
        return default
    
    def load_factor(self) -> float:
        """Calculate the current load factor (size / capacity).
        
        Returns:
            Current load factor as a float
        """
        return self._size / self._capacity
    
    def bucket_distribution(self) -> List[int]:
        """Get the distribution of items across buckets.
        
        Returns:
            List of item counts per bucket
        """
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
        """Get statistics about the hash map's distribution and performance.
        
        Returns:
            Dictionary with size, capacity, load factor, and chain statistics
        """
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
        """Convert the hash map to a standard Python dictionary.
        
        Returns:
            Dictionary representation of the hash map
        """
        return dict(self.items())
    
    @classmethod
    def from_dict(cls, d: dict) -> "HashMap":
        """Create a HashMap from a dictionary.
        
        Args:
            d: Dictionary to convert
        
        Returns:
            New HashMap instance with keys and values from the dictionary
        """
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
        """Add an item to the set.
        
        Args:
            item: Item to add
        
        Returns:
            True if item was newly added, False if it already existed
        """
        return self._map.put(item, True)
    
    def remove(self, item: Any) -> bool:
        """Remove an item from the set.
        
        Args:
            item: Item to remove
        
        Returns:
            True if item was found and removed, False otherwise
        """
        return self._map.remove(item)
    
    def discard(self, item: Any):
        """Remove an item from the set if present (no error if missing).
        
        Args:
            item: Item to remove
        """
        self._map.remove(item)
    
    def clear(self):
        """Remove all items from the set."""
        self._map.clear()
    
    def union(self, other: "HashSet") -> "HashSet":
        """Create a new set containing all items from both sets.
        
        Args:
            other: Other HashSet to union with
        
        Returns:
            New HashSet containing all unique items from both sets
        """
        result = HashSet()
        for item in self:
            result.add(item)
        for item in other:
            result.add(item)
        return result
    
    def intersection(self, other: "HashSet") -> "HashSet":
        """Create a new set containing items present in both sets.
        
        Args:
            other: Other HashSet to intersect with
        
        Returns:
            New HashSet containing items common to both sets
        """
        result = HashSet()
        for item in self:
            if item in other:
                result.add(item)
        return result
    
    def difference(self, other: "HashSet") -> "HashSet":
        """Create a new set containing items in this set but not in the other.
        
        Args:
            other: Other HashSet to compute difference with
        
        Returns:
            New HashSet containing items only in this set
        """
        result = HashSet()
        for item in self:
            if item not in other:
                result.add(item)
        return result
    
    def to_list(self) -> List[Any]:
        """Convert the set to a list.
        
        Returns:
            List containing all items in the set
        """
        return list(self)
    
    @classmethod
    def from_list(cls, items: List[Any]) -> "HashSet":
        """Create a HashSet from a list of items.
        
        Args:
            items: List of items to add to the set
        
        Returns:
            New HashSet instance containing the items
        """
        s = cls()
        for item in items:
            s.add(item)
        return s


