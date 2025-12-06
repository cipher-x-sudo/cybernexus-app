"""
Tests for Trie DSA Implementation
"""

import pytest
from app.core.dsa.trie import Trie


class TestTrie:
    """Test suite for Trie data structure."""
    
    def test_create_empty_trie(self):
        """Test creating an empty trie."""
        t = Trie()
        assert len(t) == 0
    
    def test_insert_single(self):
        """Test inserting a single key."""
        t = Trie()
        t.insert("hello", "world")
        
        assert len(t) == 1
        assert t.search("hello") == "world"
    
    def test_insert_multiple(self):
        """Test inserting multiple keys."""
        t = Trie()
        t.insert("hello", "world")
        t.insert("help", "me")
        t.insert("world", "peace")
        
        assert len(t) == 3
        assert t.search("hello") == "world"
        assert t.search("help") == "me"
        assert t.search("world") == "peace"
    
    def test_search_missing(self):
        """Test searching for missing key."""
        t = Trie()
        t.insert("hello", "world")
        
        assert t.search("missing") is None
    
    def test_search_prefix_not_word(self):
        """Test that prefix alone doesn't match."""
        t = Trie()
        t.insert("hello", "world")
        
        assert t.search("hel") is None
    
    def test_contains(self):
        """Test __contains__ operator."""
        t = Trie()
        t.insert("hello")
        
        assert "hello" in t
        assert "missing" not in t
    
    def test_delete(self):
        """Test deleting keys."""
        t = Trie()
        t.insert("hello", "world")
        t.insert("help", "me")
        
        assert t.delete("hello")
        assert len(t) == 1
        assert t.search("hello") is None
        assert t.search("help") == "me"
    
    def test_delete_missing(self):
        """Test deleting non-existent key."""
        t = Trie()
        t.insert("hello")
        
        assert not t.delete("missing")
    
    def test_starts_with(self):
        """Test prefix checking."""
        t = Trie()
        t.insert("hello")
        t.insert("help")
        t.insert("world")
        
        assert t.starts_with("hel")
        assert t.starts_with("hello")
        assert not t.starts_with("xyz")
    
    def test_count_prefix(self):
        """Test counting words with prefix."""
        t = Trie()
        t.insert("hello")
        t.insert("help")
        t.insert("helper")
        t.insert("world")
        
        assert t.count_prefix("hel") == 3
        assert t.count_prefix("help") == 2
        assert t.count_prefix("world") == 1
        assert t.count_prefix("xyz") == 0
    
    def test_get_prefix_matches(self):
        """Test getting all matches for prefix."""
        t = Trie()
        t.insert("hello", 1)
        t.insert("help", 2)
        t.insert("helper", 3)
        t.insert("world", 4)
        
        matches = t.get_prefix_matches("hel")
        keys = [k for k, v in matches]
        
        assert len(keys) == 3
        assert "hello" in keys
        assert "help" in keys
        assert "helper" in keys
    
    def test_autocomplete(self):
        """Test autocomplete suggestions."""
        t = Trie()
        t.insert("hello")
        t.insert("help")
        t.insert("helper")
        t.insert("world")
        
        suggestions = t.autocomplete("hel", limit=2)
        
        assert len(suggestions) == 2
    
    def test_match_pattern(self):
        """Test wildcard pattern matching."""
        t = Trie()
        t.insert("cat", 1)
        t.insert("car", 2)
        t.insert("bat", 3)
        
        matches = t.match_pattern("c*t")  # * matches any single char
        keys = [k for k, v in matches]
        
        assert "cat" in keys
        assert len(keys) == 1
    
    def test_get_longest_prefix(self):
        """Test finding longest matching prefix."""
        t = Trie()
        t.insert("a", 1)
        t.insert("ab", 2)
        t.insert("abc", 3)
        
        result = t.get_longest_prefix("abcd")
        
        assert result == ("abc", 3)
    
    def test_find_all_in_text(self):
        """Test finding all keys in text."""
        t = Trie()
        t.insert("cat", 1)
        t.insert("at", 2)
        
        matches = t.find_all_in_text("a cat sat")
        
        assert len(matches) >= 2  # Should find "cat" and "at"
    
    def test_keys(self):
        """Test iterating over all keys."""
        t = Trie()
        t.insert("hello")
        t.insert("help")
        t.insert("world")
        
        keys = list(t.keys())
        
        assert len(keys) == 3
        assert set(keys) == {"hello", "help", "world"}
    
    def test_values(self):
        """Test iterating over all values."""
        t = Trie()
        t.insert("hello", 1)
        t.insert("help", 2)
        
        values = list(t.values())
        
        assert set(values) == {1, 2}
    
    def test_items(self):
        """Test iterating over key-value pairs."""
        t = Trie()
        t.insert("hello", 1)
        t.insert("help", 2)
        
        items = list(t.items())
        
        assert len(items) == 2
    
    def test_clear(self):
        """Test clearing the trie."""
        t = Trie()
        t.insert("hello")
        t.insert("help")
        
        t.clear()
        
        assert len(t) == 0
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        d = {"hello": 1, "help": 2}
        t = Trie.from_dict(d)
        
        assert len(t) == 2
        assert t.search("hello") == 1
    
    def test_from_list(self):
        """Test creating from list."""
        keys = ["hello", "help", "world"]
        t = Trie.from_list(keys)
        
        assert len(t) == 3
        assert "hello" in t
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        t = Trie()
        t.insert("hello", 1)
        t.insert("help", 2)
        
        d = t.to_dict()
        
        assert d == {"hello": 1, "help": 2}
    
    def test_case_sensitivity(self):
        """Test that trie is case-sensitive."""
        t = Trie()
        t.insert("Hello", 1)
        
        assert t.search("Hello") == 1
        assert t.search("hello") is None


