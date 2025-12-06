"""
Custom HashMap Implementation

Hash table with separate chaining for O(1) average-case lookups.

Used for:
- Fast entity correlation
- Caching DNS lookups
- Username/email to breach mappings
"""

from typing import Any, Optional, List, Tuple, Generator, Callable
from dataclasses import dataclass


@dataclass
class HashNode:
    """Node in hash bucket linked list."""
    key: Any
    value: Any
    next: Optional["HashNode"] = None


class HashMap:
    """
    HashMap with separate chaining collision resolution.
    
    Features:
    - O(1) average-case insert, search, delete
    - Automatic resizing when load factor exceeds threshold
    - Supports any hashable keys
    - Iteration over keys, values, and items
    """
    
    DEFAULT_CAPACITY = 16
    LOAD_FACTOR_THRESHOLD = 0.75
    
    def __init__(self, capacity: int = None):
        """Initialize HashMap.
        
        Args:
            capacity: Initial capacity (default 16)
        """
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
    
    # ==================== Core Operations ====================
    
    def _hash(self, key: Any) -> int:
        """Compute hash index for a key."""
        return hash(key) % self._capacity
    
    def _resize(self):
        """Resize the hash table when load factor exceeds threshold."""
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = [None] * self._capacity
        self._size = 0
        
        # Rehash all existing entries
        for bucket in old_buckets:
            node = bucket
            while node:
                self.put(node.key, node.value)
                node = node.next
    
    def put(self, key: Any, value: Any) -> bool:
        """Insert or update a key-value pair.
        
        Args:
            key: The key to insert
            value: The value to associate with the key
            
        Returns:
            True if new key inserted, False if existing key updated
        """
        # Check load factor and resize if necessary
        if self._size / self._capacity >= self.LOAD_FACTOR_THRESHOLD:
            self._resize()
        
        index = self._hash(key)
        node = self._buckets[index]
        
        # Search for existing key in bucket
        while node:
            if node.key == key:
                node.value = value  # Update existing
                return False
            node = node.next
        
        # Insert new node at head of bucket
        new_node = HashNode(key=key, value=value, next=self._buckets[index])
        self._buckets[index] = new_node
        self._size += 1
        return True
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Get value for a key.
        
        Args:
            key: The key to look up
            default: Value to return if key not found
            
        Returns:
            The value if found, default otherwise
        """
        index = self._hash(key)
        node = self._buckets[index]
        
        while node:
            if node.key == key:
                return node.value
            node = node.next
        
        return default
    
    def remove(self, key: Any) -> bool:
        """Remove a key from the map.
        
        Args:
            key: The key to remove
            
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
    
    # ==================== Iteration ====================
    
    def keys(self) -> Generator[Any, None, None]:
        """Iterate over all keys."""
        for bucket in self._buckets:
            node = bucket
            while node:
                yield node.key
                node = node.next
    
    def values(self) -> Generator[Any, None, None]:
        """Iterate over all values."""
        for bucket in self._buckets:
            node = bucket
            while node:
                yield node.value
                node = node.next
    
    def items(self) -> Generator[Tuple[Any, Any], None, None]:
        """Iterate over all key-value pairs."""
        for bucket in self._buckets:
            node = bucket
            while node:
                yield (node.key, node.value)
                node = node.next
    
    # ==================== Utility ====================
    
    def clear(self):
        """Remove all items from the map."""
        self._buckets = [None] * self._capacity
        self._size = 0
    
    def update(self, other: dict = None, **kwargs):
        """Update map with items from another dict or keyword arguments."""
        if other:
            for key, value in other.items():
                self.put(key, value)
        for key, value in kwargs.items():
            self.put(key, value)
    
    def setdefault(self, key: Any, default: Any = None) -> Any:
        """Get value for key, setting it to default if not present."""
        value = self.get(key)
        if value is None:
            self.put(key, default)
            return default
        return value
    
    def pop(self, key: Any, default: Any = None) -> Any:
        """Remove and return value for key."""
        value = self.get(key)
        if value is not None:
            self.remove(key)
            return value
        return default
    
    # ==================== Statistics ====================
    
    def load_factor(self) -> float:
        """Get current load factor."""
        return self._size / self._capacity
    
    def bucket_distribution(self) -> List[int]:
        """Get number of items in each bucket (for analysis)."""
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
        """Get hashmap statistics."""
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
    
    # ==================== Serialization ====================
    
    def to_dict(self) -> dict:
        """Convert to regular Python dict."""
        return dict(self.items())
    
    @classmethod
    def from_dict(cls, d: dict) -> "HashMap":
        """Create HashMap from regular dict."""
        hashmap = cls()
        for key, value in d.items():
            hashmap.put(key, value)
        return hashmap


class HashSet:
    """
    HashSet implementation using HashMap.
    
    Features:
    - O(1) average-case add, contains, remove
    - No duplicate values
    """
    
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
        
        Returns:
            True if item was added, False if already present
        """
        return self._map.put(item, True)
    
    def remove(self, item: Any) -> bool:
        """Remove an item from the set.
        
        Returns:
            True if item was removed, False if not present
        """
        return self._map.remove(item)
    
    def discard(self, item: Any):
        """Remove item if present (no error if not)."""
        self._map.remove(item)
    
    def clear(self):
        """Remove all items."""
        self._map.clear()
    
    def union(self, other: "HashSet") -> "HashSet":
        """Return union of two sets."""
        result = HashSet()
        for item in self:
            result.add(item)
        for item in other:
            result.add(item)
        return result
    
    def intersection(self, other: "HashSet") -> "HashSet":
        """Return intersection of two sets."""
        result = HashSet()
        for item in self:
            if item in other:
                result.add(item)
        return result
    
    def difference(self, other: "HashSet") -> "HashSet":
        """Return difference (self - other)."""
        result = HashSet()
        for item in self:
            if item not in other:
                result.add(item)
        return result
    
    def to_list(self) -> List[Any]:
        """Convert to list."""
        return list(self)
    
    @classmethod
    def from_list(cls, items: List[Any]) -> "HashSet":
        """Create set from list."""
        s = cls()
        for item in items:
            s.add(item)
        return s


