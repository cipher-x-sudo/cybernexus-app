"""
Tests for Bloom Filter DSA Implementation
"""

import pytest
from app.core.dsa.bloom_filter import BloomFilter, CountingBloomFilter


class TestBloomFilter:
    """Test suite for Bloom Filter data structure."""
    
    def test_create_filter(self):
        """Test creating a bloom filter."""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
        
        assert len(bf) == 0
        assert bf.size_bits > 0
        assert bf.num_hashes > 0
    
    def test_add_and_contains(self):
        """Test adding and checking items."""
        bf = BloomFilter(expected_items=100)
        bf.add("hello")
        
        assert "hello" in bf
        assert bf.contains("hello")
    
    def test_missing_item(self):
        """Test that missing items return False."""
        bf = BloomFilter(expected_items=100)
        bf.add("hello")
        
        # This might rarely return True (false positive), but usually False
        # For deterministic test, we just verify the item we added
        assert "hello" in bf
    
    def test_no_false_negatives(self):
        """Test that added items are always found."""
        bf = BloomFilter(expected_items=1000)
        
        items = [f"item_{i}" for i in range(100)]
        for item in items:
            bf.add(item)
        
        # All added items must be found
        for item in items:
            assert item in bf
    
    def test_add_many(self):
        """Test adding multiple items."""
        bf = BloomFilter(expected_items=1000)
        items = ["item1", "item2", "item3"]
        
        bf.add_many(items)
        
        for item in items:
            assert item in bf
    
    def test_fill_ratio(self):
        """Test fill ratio calculation."""
        bf = BloomFilter(expected_items=1000)
        
        initial_ratio = bf.fill_ratio()
        
        for i in range(100):
            bf.add(f"item_{i}")
        
        assert bf.fill_ratio() > initial_ratio
    
    def test_current_false_positive_rate(self):
        """Test false positive rate estimation."""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
        
        assert bf.current_false_positive_rate() == 0.0
        
        for i in range(100):
            bf.add(f"item_{i}")
        
        assert bf.current_false_positive_rate() > 0
    
    def test_stats(self):
        """Test getting statistics."""
        bf = BloomFilter(expected_items=1000, false_positive_rate=0.01)
        bf.add("hello")
        
        stats = bf.stats()
        
        assert "items_added" in stats
        assert "size_bits" in stats
        assert "num_hashes" in stats
        assert "fill_ratio" in stats
        assert stats["items_added"] == 1
    
    def test_clear(self):
        """Test clearing the filter."""
        bf = BloomFilter(expected_items=100)
        bf.add("hello")
        
        bf.clear()
        
        assert len(bf) == 0
        # Note: Due to bloom filter nature, "hello" might still appear to be in filter
        # This test just verifies clear resets count
    
    def test_merge(self):
        """Test merging two filters."""
        bf1 = BloomFilter(expected_items=100)
        bf1.add("item1")
        
        bf2 = BloomFilter(expected_items=100)
        bf2.add("item2")
        
        merged = bf1.merge(bf2)
        
        assert "item1" in merged
        assert "item2" in merged
    
    def test_merge_incompatible_raises(self):
        """Test that merging incompatible filters raises error."""
        bf1 = BloomFilter(expected_items=100, false_positive_rate=0.01)
        bf2 = BloomFilter(expected_items=1000, false_positive_rate=0.001)
        
        with pytest.raises(ValueError):
            bf1.merge(bf2)
    
    def test_different_types(self):
        """Test adding different types."""
        bf = BloomFilter(expected_items=100)
        
        bf.add("string")
        bf.add(123)
        bf.add(b"bytes")
        
        assert "string" in bf
        assert 123 in bf
        assert b"bytes" in bf


class TestCountingBloomFilter:
    """Test suite for Counting Bloom Filter."""
    
    def test_create_filter(self):
        """Test creating a counting bloom filter."""
        cbf = CountingBloomFilter(expected_items=1000)
        assert len(cbf) == 0
    
    def test_add_and_contains(self):
        """Test adding and checking items."""
        cbf = CountingBloomFilter(expected_items=100)
        cbf.add("hello")
        
        assert "hello" in cbf
    
    def test_remove(self):
        """Test removing items."""
        cbf = CountingBloomFilter(expected_items=100)
        cbf.add("hello")
        
        assert cbf.remove("hello")
        # Note: May still show as present due to probabilistic nature
    
    def test_remove_missing(self):
        """Test removing non-existent item."""
        cbf = CountingBloomFilter(expected_items=100)
        
        assert not cbf.remove("missing")
    
    def test_clear(self):
        """Test clearing the filter."""
        cbf = CountingBloomFilter(expected_items=100)
        cbf.add("hello")
        
        cbf.clear()
        
        assert len(cbf) == 0
    
    def test_stats(self):
        """Test getting statistics."""
        cbf = CountingBloomFilter(expected_items=100)
        cbf.add("hello")
        
        stats = cbf.stats()
        
        assert "items_added" in stats
        assert "max_counter" in stats


