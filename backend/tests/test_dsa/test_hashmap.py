"""
Tests for HashMap DSA Implementation
"""

import pytest
from app.core.dsa.hashmap import HashMap, HashSet


class TestHashMap:
    """Test suite for HashMap data structure."""
    
    def test_create_empty_map(self):
        """Test creating an empty map."""
        m = HashMap()
        assert len(m) == 0
    
    def test_put_get(self):
        """Test basic put and get."""
        m = HashMap()
        m.put("key1", "value1")
        
        assert m.get("key1") == "value1"
        assert len(m) == 1
    
    def test_put_multiple(self):
        """Test putting multiple items."""
        m = HashMap()
        m.put("key1", "value1")
        m.put("key2", "value2")
        m.put("key3", "value3")
        
        assert len(m) == 3
        assert m.get("key1") == "value1"
        assert m.get("key2") == "value2"
        assert m.get("key3") == "value3"
    
    def test_put_update(self):
        """Test that put updates existing key."""
        m = HashMap()
        m.put("key1", "value1")
        result = m.put("key1", "updated")
        
        assert not result  # Returns False for update
        assert m.get("key1") == "updated"
        assert len(m) == 1
    
    def test_get_missing(self):
        """Test getting non-existent key."""
        m = HashMap()
        m.put("key1", "value1")
        
        assert m.get("missing") is None
        assert m.get("missing", "default") == "default"
    
    def test_remove(self):
        """Test removing items."""
        m = HashMap()
        m.put("key1", "value1")
        m.put("key2", "value2")
        
        assert m.remove("key1")
        assert len(m) == 1
        assert m.get("key1") is None
    
    def test_remove_missing(self):
        """Test removing non-existent key."""
        m = HashMap()
        m.put("key1", "value1")
        
        assert not m.remove("missing")
    
    def test_contains(self):
        """Test __contains__ operator."""
        m = HashMap()
        m.put("key1", "value1")
        
        assert "key1" in m
        assert "missing" not in m
    
    def test_getitem_setitem(self):
        """Test bracket notation."""
        m = HashMap()
        m["key1"] = "value1"
        
        assert m["key1"] == "value1"
    
    def test_getitem_missing(self):
        """Test bracket notation for missing key."""
        m = HashMap()
        
        with pytest.raises(KeyError):
            _ = m["missing"]
    
    def test_delitem(self):
        """Test delete with bracket notation."""
        m = HashMap()
        m["key1"] = "value1"
        
        del m["key1"]
        assert "key1" not in m
    
    def test_keys(self):
        """Test iterating over keys."""
        m = HashMap()
        m.put("key1", "value1")
        m.put("key2", "value2")
        
        keys = list(m.keys())
        
        assert len(keys) == 2
        assert set(keys) == {"key1", "key2"}
    
    def test_values(self):
        """Test iterating over values."""
        m = HashMap()
        m.put("key1", "value1")
        m.put("key2", "value2")
        
        values = list(m.values())
        
        assert len(values) == 2
        assert set(values) == {"value1", "value2"}
    
    def test_items(self):
        """Test iterating over items."""
        m = HashMap()
        m.put("key1", "value1")
        m.put("key2", "value2")
        
        items = list(m.items())
        
        assert len(items) == 2
        assert set(items) == {("key1", "value1"), ("key2", "value2")}
    
    def test_iteration(self):
        """Test iterating over map (yields keys)."""
        m = HashMap()
        m.put("key1", "value1")
        m.put("key2", "value2")
        
        keys = list(m)
        
        assert len(keys) == 2
    
    def test_clear(self):
        """Test clearing the map."""
        m = HashMap()
        m.put("key1", "value1")
        m.put("key2", "value2")
        
        m.clear()
        
        assert len(m) == 0
    
    def test_update_dict(self):
        """Test update from dict."""
        m = HashMap()
        m.update({"key1": "value1", "key2": "value2"})
        
        assert len(m) == 2
        assert m.get("key1") == "value1"
    
    def test_update_kwargs(self):
        """Test update from kwargs."""
        m = HashMap()
        m.update(key1="value1", key2="value2")
        
        assert len(m) == 2
    
    def test_setdefault(self):
        """Test setdefault method."""
        m = HashMap()
        
        # Key doesn't exist
        result = m.setdefault("key1", "default")
        assert result == "default"
        assert m.get("key1") == "default"
        
        # Key exists
        result = m.setdefault("key1", "new_default")
        assert result == "default"
    
    def test_pop(self):
        """Test pop method."""
        m = HashMap()
        m.put("key1", "value1")
        
        result = m.pop("key1")
        assert result == "value1"
        assert "key1" not in m
        
        # Pop missing with default
        result = m.pop("missing", "default")
        assert result == "default"
    
    def test_resize(self):
        """Test automatic resizing."""
        m = HashMap(capacity=4)
        
        # Add enough items to trigger resize
        for i in range(10):
            m.put(f"key{i}", f"value{i}")
        
        assert len(m) == 10
        # All items should still be accessible
        for i in range(10):
            assert m.get(f"key{i}") == f"value{i}"
    
    def test_load_factor(self):
        """Test load factor calculation."""
        m = HashMap(capacity=10)
        
        for i in range(5):
            m.put(f"key{i}", f"value{i}")
        
        assert m.load_factor() == 0.5
    
    def test_stats(self):
        """Test getting statistics."""
        m = HashMap()
        for i in range(10):
            m.put(f"key{i}", f"value{i}")
        
        stats = m.stats()
        
        assert stats["size"] == 10
        assert "capacity" in stats
        assert "load_factor" in stats
    
    def test_to_dict(self):
        """Test converting to dict."""
        m = HashMap()
        m.put("key1", "value1")
        m.put("key2", "value2")
        
        d = m.to_dict()
        
        assert d == {"key1": "value1", "key2": "value2"}
    
    def test_from_dict(self):
        """Test creating from dict."""
        d = {"key1": "value1", "key2": "value2"}
        m = HashMap.from_dict(d)
        
        assert len(m) == 2
        assert m.get("key1") == "value1"
    
    def test_collision_handling(self):
        """Test that collisions are handled correctly."""
        m = HashMap(capacity=4)  # Small capacity to force collisions
        
        # Add items that might collide
        m.put("a", 1)
        m.put("b", 2)
        m.put("c", 3)
        m.put("d", 4)
        m.put("e", 5)
        
        # All items should be retrievable
        assert m.get("a") == 1
        assert m.get("b") == 2
        assert m.get("c") == 3
        assert m.get("d") == 4
        assert m.get("e") == 5


class TestHashSet:
    """Test suite for HashSet data structure."""
    
    def test_create_empty_set(self):
        """Test creating an empty set."""
        s = HashSet()
        assert len(s) == 0
    
    def test_add(self):
        """Test adding items."""
        s = HashSet()
        s.add("item1")
        s.add("item2")
        
        assert len(s) == 2
        assert "item1" in s
        assert "item2" in s
    
    def test_add_duplicate(self):
        """Test adding duplicate returns False."""
        s = HashSet()
        assert s.add("item1")
        assert not s.add("item1")
        assert len(s) == 1
    
    def test_remove(self):
        """Test removing items."""
        s = HashSet()
        s.add("item1")
        
        assert s.remove("item1")
        assert len(s) == 0
    
    def test_discard(self):
        """Test discard (no error on missing)."""
        s = HashSet()
        s.add("item1")
        
        s.discard("item1")
        s.discard("missing")  # Should not raise
        
        assert len(s) == 0
    
    def test_union(self):
        """Test union operation."""
        s1 = HashSet()
        s1.add("a")
        s1.add("b")
        
        s2 = HashSet()
        s2.add("b")
        s2.add("c")
        
        result = s1.union(s2)
        
        assert len(result) == 3
        assert "a" in result
        assert "b" in result
        assert "c" in result
    
    def test_intersection(self):
        """Test intersection operation."""
        s1 = HashSet()
        s1.add("a")
        s1.add("b")
        
        s2 = HashSet()
        s2.add("b")
        s2.add("c")
        
        result = s1.intersection(s2)
        
        assert len(result) == 1
        assert "b" in result
    
    def test_difference(self):
        """Test difference operation."""
        s1 = HashSet()
        s1.add("a")
        s1.add("b")
        
        s2 = HashSet()
        s2.add("b")
        s2.add("c")
        
        result = s1.difference(s2)
        
        assert len(result) == 1
        assert "a" in result
    
    def test_to_list(self):
        """Test converting to list."""
        s = HashSet()
        s.add("a")
        s.add("b")
        
        lst = s.to_list()
        
        assert len(lst) == 2
        assert set(lst) == {"a", "b"}
    
    def test_from_list(self):
        """Test creating from list."""
        s = HashSet.from_list(["a", "b", "c"])
        
        assert len(s) == 3


