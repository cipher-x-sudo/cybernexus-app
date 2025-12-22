"""Bloom Filter implementation.

This module implements a probabilistic data structure for membership testing.
Provides memory-efficient way to check if an element is possibly in a set,
with configurable false positive rate.

DSA Concept: Bloom Filter
- Probabilistic membership testing
- Configurable false positive rate
- Memory efficient O(m) space where m is bit array size
- O(k) insert and query operations where k is number of hash functions
- No false negatives, possible false positives
"""

import math
import hashlib
from typing import Any, List


class BloomFilter:
    
    def __init__(self, expected_items: int, false_positive_rate: float = 0.01):
        if expected_items <= 0:
            raise ValueError("Expected items must be positive")
        if not 0 < false_positive_rate < 1:
            raise ValueError("False positive rate must be between 0 and 1")
        
        self._size = self._optimal_size(expected_items, false_positive_rate)
        
        self._num_hashes = self._optimal_hashes(self._size, expected_items)
        
        self._bit_array = [False] * self._size
        
        self._count = 0
        self._expected_items = expected_items
        self._false_positive_rate = false_positive_rate
    
    @staticmethod
    def _optimal_size(n: int, p: float) -> int:
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(math.ceil(m))
    
    @staticmethod
    def _optimal_hashes(m: int, n: int) -> int:
        k = (m / n) * math.log(2)
        return max(1, int(round(k)))
    
    def _get_hashes(self, item: Any) -> List[int]:
        if isinstance(item, str):
            data = item.encode('utf-8')
        elif isinstance(item, bytes):
            data = item
        else:
            data = str(item).encode('utf-8')
        
        h1 = int(hashlib.md5(data).hexdigest(), 16)
        h2 = int(hashlib.sha256(data).hexdigest(), 16)
        
        hashes = []
        for i in range(self._num_hashes):
            combined = (h1 + i * h2) % self._size
            hashes.append(combined)
        
        return hashes
    
    def add(self, item: Any):
        for hash_val in self._get_hashes(item):
            self._bit_array[hash_val] = True
        self._count += 1
    
    def __contains__(self, item: Any) -> bool:
        return self.contains(item)
    
    def contains(self, item: Any) -> bool:
        for hash_val in self._get_hashes(item):
            if not self._bit_array[hash_val]:
                return False
        return True
    
    def add_many(self, items: List[Any]):
        for item in items:
            self.add(item)
    
    def __len__(self) -> int:
        return self._count
    
    @property
    def size_bits(self) -> int:
        return self._size
    
    @property
    def size_bytes(self) -> int:
        return self._size // 8 + 1
    
    @property
    def num_hashes(self) -> int:
        return self._num_hashes
    
    def current_false_positive_rate(self) -> float:
        if self._count == 0:
            return 0.0
        
        exponent = -self._num_hashes * self._count / self._size
        return (1 - math.exp(exponent)) ** self._num_hashes
    
    def fill_ratio(self) -> float:
        return sum(self._bit_array) / self._size
    
    def stats(self) -> dict:
        return {
            "items_added": self._count,
            "expected_items": self._expected_items,
            "size_bits": self._size,
            "size_bytes": self.size_bytes,
            "num_hashes": self._num_hashes,
            "fill_ratio": self.fill_ratio(),
            "target_fpr": self._false_positive_rate,
            "current_fpr": self.current_false_positive_rate()
        }
    
    def clear(self):
        self._bit_array = [False] * self._size
        self._count = 0
    
    def merge(self, other: "BloomFilter") -> "BloomFilter":
        if self._size != other._size or self._num_hashes != other._num_hashes:
            raise ValueError("Bloom filters must have same size and hash count")
        
        result = BloomFilter(self._expected_items, self._false_positive_rate)
        result._bit_array = [a or b for a, b in zip(self._bit_array, other._bit_array)]
        result._count = self._count + other._count
        
        return result


class CountingBloomFilter:
    
    def __init__(self, expected_items: int, false_positive_rate: float = 0.01):
        if expected_items <= 0:
            raise ValueError("Expected items must be positive")
        if not 0 < false_positive_rate < 1:
            raise ValueError("False positive rate must be between 0 and 1")
        
        self._size = BloomFilter._optimal_size(expected_items, false_positive_rate)
        self._num_hashes = BloomFilter._optimal_hashes(self._size, expected_items)
        
        self._counters = [0] * self._size
        self._count = 0
        self._expected_items = expected_items
        self._false_positive_rate = false_positive_rate
    
    def _get_hashes(self, item: Any) -> List[int]:
        if isinstance(item, str):
            data = item.encode('utf-8')
        elif isinstance(item, bytes):
            data = item
        else:
            data = str(item).encode('utf-8')
        
        h1 = int(hashlib.md5(data).hexdigest(), 16)
        h2 = int(hashlib.sha256(data).hexdigest(), 16)
        
        hashes = []
        for i in range(self._num_hashes):
            combined = (h1 + i * h2) % self._size
            hashes.append(combined)
        
        return hashes
    
    def add(self, item: Any):
        for hash_val in self._get_hashes(item):
            self._counters[hash_val] += 1
        self._count += 1
    
    def remove(self, item: Any) -> bool:
        hashes = self._get_hashes(item)
        
        if not all(self._counters[h] > 0 for h in hashes):
            return False
        
        for hash_val in hashes:
            self._counters[hash_val] = max(0, self._counters[hash_val] - 1)
        
        self._count = max(0, self._count - 1)
        return True
    
    def __contains__(self, item: Any) -> bool:
        return all(self._counters[h] > 0 for h in self._get_hashes(item))
    
    def contains(self, item: Any) -> bool:
        return item in self
    
    def __len__(self) -> int:
        return self._count
    
    def clear(self):
        self._counters = [0] * self._size
        self._count = 0
    
    def stats(self) -> dict:
        non_zero = sum(1 for c in self._counters if c > 0)
        return {
            "items_added": self._count,
            "size_counters": self._size,
            "num_hashes": self._num_hashes,
            "fill_ratio": non_zero / self._size,
            "max_counter": max(self._counters) if self._counters else 0
        }


