"""
Custom Bloom Filter Implementation

Probabilistic data structure for fast membership testing.

Used for:
- Fast URL deduplication during crawling
- Quick "have we seen this?" checks
- Reducing lookups to slower storage
"""

import math
import hashlib
from typing import Any, List


class BloomFilter:
    """
    Bloom Filter - Probabilistic Set Membership Testing.
    
    Features:
    - O(k) insert and query where k = number of hash functions
    - No false negatives (if it says "no", it's definitely no)
    - Small false positive rate (configurable)
    - Very memory efficient
    
    Trade-offs:
    - Cannot delete items
    - May have false positives
    - Cannot enumerate items
    """
    
    def __init__(self, expected_items: int, false_positive_rate: float = 0.01):
        """Initialize Bloom Filter.
        
        Args:
            expected_items: Expected number of items to store
            false_positive_rate: Desired false positive rate (0-1)
        """
        if expected_items <= 0:
            raise ValueError("Expected items must be positive")
        if not 0 < false_positive_rate < 1:
            raise ValueError("False positive rate must be between 0 and 1")
        
        # Calculate optimal size and number of hash functions
        # m = -(n * ln(p)) / (ln(2)^2)
        self._size = self._optimal_size(expected_items, false_positive_rate)
        
        # k = (m/n) * ln(2)
        self._num_hashes = self._optimal_hashes(self._size, expected_items)
        
        # Initialize bit array
        self._bit_array = [False] * self._size
        
        self._count = 0
        self._expected_items = expected_items
        self._false_positive_rate = false_positive_rate
    
    @staticmethod
    def _optimal_size(n: int, p: float) -> int:
        """Calculate optimal bit array size."""
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(math.ceil(m))
    
    @staticmethod
    def _optimal_hashes(m: int, n: int) -> int:
        """Calculate optimal number of hash functions."""
        k = (m / n) * math.log(2)
        return max(1, int(round(k)))
    
    def _get_hashes(self, item: Any) -> List[int]:
        """Get hash values for an item.
        
        Uses double hashing technique to generate k hash values
        from two base hashes.
        """
        # Convert item to bytes
        if isinstance(item, str):
            data = item.encode('utf-8')
        elif isinstance(item, bytes):
            data = item
        else:
            data = str(item).encode('utf-8')
        
        # Generate two base hashes
        h1 = int(hashlib.md5(data).hexdigest(), 16)
        h2 = int(hashlib.sha256(data).hexdigest(), 16)
        
        # Generate k hash values using double hashing
        hashes = []
        for i in range(self._num_hashes):
            combined = (h1 + i * h2) % self._size
            hashes.append(combined)
        
        return hashes
    
    def add(self, item: Any):
        """Add an item to the filter.
        
        Args:
            item: Item to add (will be converted to string if needed)
        """
        for hash_val in self._get_hashes(item):
            self._bit_array[hash_val] = True
        self._count += 1
    
    def __contains__(self, item: Any) -> bool:
        """Check if item might be in the filter.
        
        Args:
            item: Item to check
            
        Returns:
            False = definitely not in filter
            True = probably in filter (may be false positive)
        """
        return self.contains(item)
    
    def contains(self, item: Any) -> bool:
        """Check if item might be in the filter."""
        for hash_val in self._get_hashes(item):
            if not self._bit_array[hash_val]:
                return False
        return True
    
    def add_many(self, items: List[Any]):
        """Add multiple items."""
        for item in items:
            self.add(item)
    
    def __len__(self) -> int:
        """Return number of items added (not unique items)."""
        return self._count
    
    @property
    def size_bits(self) -> int:
        """Get size of bit array."""
        return self._size
    
    @property
    def size_bytes(self) -> int:
        """Get approximate size in bytes."""
        return self._size // 8 + 1
    
    @property
    def num_hashes(self) -> int:
        """Get number of hash functions."""
        return self._num_hashes
    
    def current_false_positive_rate(self) -> float:
        """Estimate current false positive rate.
        
        Returns:
            Estimated false positive probability
        """
        # p = (1 - e^(-kn/m))^k
        if self._count == 0:
            return 0.0
        
        exponent = -self._num_hashes * self._count / self._size
        return (1 - math.exp(exponent)) ** self._num_hashes
    
    def fill_ratio(self) -> float:
        """Get ratio of bits set to 1."""
        return sum(self._bit_array) / self._size
    
    def stats(self) -> dict:
        """Get filter statistics."""
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
        """Reset the filter."""
        self._bit_array = [False] * self._size
        self._count = 0
    
    def merge(self, other: "BloomFilter") -> "BloomFilter":
        """Merge two bloom filters (union).
        
        Both filters must have same size and number of hashes.
        
        Returns:
            New merged BloomFilter
        """
        if self._size != other._size or self._num_hashes != other._num_hashes:
            raise ValueError("Bloom filters must have same size and hash count")
        
        result = BloomFilter(self._expected_items, self._false_positive_rate)
        result._bit_array = [a or b for a, b in zip(self._bit_array, other._bit_array)]
        result._count = self._count + other._count
        
        return result


class CountingBloomFilter:
    """
    Counting Bloom Filter - Allows deletion.
    
    Uses counters instead of bits, allowing items to be removed.
    Uses more memory but supports deletions.
    """
    
    def __init__(self, expected_items: int, false_positive_rate: float = 0.01):
        """Initialize Counting Bloom Filter."""
        if expected_items <= 0:
            raise ValueError("Expected items must be positive")
        if not 0 < false_positive_rate < 1:
            raise ValueError("False positive rate must be between 0 and 1")
        
        self._size = BloomFilter._optimal_size(expected_items, false_positive_rate)
        self._num_hashes = BloomFilter._optimal_hashes(self._size, expected_items)
        
        # Use counters instead of bits
        self._counters = [0] * self._size
        self._count = 0
        self._expected_items = expected_items
        self._false_positive_rate = false_positive_rate
    
    def _get_hashes(self, item: Any) -> List[int]:
        """Get hash values for an item."""
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
        """Add an item."""
        for hash_val in self._get_hashes(item):
            self._counters[hash_val] += 1
        self._count += 1
    
    def remove(self, item: Any) -> bool:
        """Remove an item.
        
        Returns:
            True if item was probably present and removed
        """
        hashes = self._get_hashes(item)
        
        # Check if item is present
        if not all(self._counters[h] > 0 for h in hashes):
            return False
        
        # Decrement counters
        for hash_val in hashes:
            self._counters[hash_val] = max(0, self._counters[hash_val] - 1)
        
        self._count = max(0, self._count - 1)
        return True
    
    def __contains__(self, item: Any) -> bool:
        """Check if item might be in filter."""
        return all(self._counters[h] > 0 for h in self._get_hashes(item))
    
    def contains(self, item: Any) -> bool:
        """Check if item might be in filter."""
        return item in self
    
    def __len__(self) -> int:
        return self._count
    
    def clear(self):
        """Reset the filter."""
        self._counters = [0] * self._size
        self._count = 0
    
    def stats(self) -> dict:
        """Get filter statistics."""
        non_zero = sum(1 for c in self._counters if c > 0)
        return {
            "items_added": self._count,
            "size_counters": self._size,
            "num_hashes": self._num_hashes,
            "fill_ratio": non_zero / self._size,
            "max_counter": max(self._counters) if self._counters else 0
        }


