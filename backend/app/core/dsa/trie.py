"""Trie (Prefix Tree) implementation.

This module implements a trie data structure for efficient prefix matching and
autocomplete functionality. Supports pattern matching with wildcards and word
count statistics.

DSA Concept: Trie (Prefix Tree)
- Prefix matching with O(m) complexity where m is key length
- Autocomplete suggestions
- Pattern matching with wildcards
- Word count statistics
- O(m) insert and search operations
- O(m + k) prefix match where k is number of results
"""

from typing import Any, Optional, List, Dict, Generator, Tuple
from dataclasses import dataclass, field


@dataclass
class TrieNode:
    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    is_end: bool = False
    value: Any = None
    count: int = 0


class Trie:
    
    def __init__(self):
        self._root = TrieNode()
        self._size = 0
    
    def __len__(self) -> int:
        return self._size
    
    def __contains__(self, key: str) -> bool:
        return self.search(key) is not None
    
    def __iter__(self) -> Generator[str, None, None]:
        yield from self.keys()
    
    def insert(self, key: str, value: Any = None) -> bool:
        """Insert a key-value pair into the trie.
        
        DSA-USED:
        - Trie: O(m) insertion where m is key length
        
        Args:
            key: String key to insert
            value: Value to associate with key (defaults to True)
        
        Returns:
            True if key was newly inserted, False if it already existed
        """
        if not key:
            return False
        
        if value is None:
            value = True
        
        node = self._root
        
        for char in key:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.count += 1
        
        is_new = not node.is_end
        node.is_end = True
        node.value = value
        
        if is_new:
            self._size += 1
        
        return is_new
    
    def search(self, key: str) -> Optional[Any]:
        """Search for a key in the trie.
        
        DSA-USED:
        - Trie: O(m) search where m is key length
        
        Args:
            key: String key to search for
        
        Returns:
            Associated value if key exists, None otherwise
        """
        node = self._find_node(key)
        
        if node and node.is_end:
            return node.value
        return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from the trie.
        
        DSA-USED:
        - Trie: O(m) deletion with recursive cleanup where m is key length
        
        Args:
            key: String key to delete
        
        Returns:
            True if key was found and deleted, False otherwise
        """
        if not key:
            return False
        
        def _delete(node: TrieNode, key: str, depth: int) -> Tuple[bool, bool]:
            if depth == len(key):
                if not node.is_end:
                    return False, False
                
                node.is_end = False
                node.value = None
                return True, len(node.children) == 0
            
            char = key[depth]
            if char not in node.children:
                return False, False
            
            found, should_delete = _delete(node.children[char], key, depth + 1)
            
            if found:
                node.children[char].count -= 1
                
                if should_delete:
                    del node.children[char]
            
            return found, len(node.children) == 0 and not node.is_end
        
        found, _ = _delete(self._root, key, 0)
        
        if found:
            self._size -= 1
        
        return found
    
    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """Find the node corresponding to a prefix.
        
        Args:
            prefix: String prefix to search for
        
        Returns:
            TrieNode if prefix exists, None otherwise
        """
        node = self._root
        
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        
        return node
    
    def starts_with(self, prefix: str) -> bool:
        """Check if any key in the trie starts with the given prefix.
        
        Args:
            prefix: Prefix string to check
        
        Returns:
            True if prefix exists in trie, False otherwise
        """
        return self._find_node(prefix) is not None
    
    def count_prefix(self, prefix: str) -> int:
        """Count how many keys have the given prefix.
        
        Args:
            prefix: Prefix string to count
        
        Returns:
            Number of keys with the given prefix
        """
        node = self._find_node(prefix)
        return node.count if node else 0
    
    def get_prefix_matches(self, prefix: str, limit: int = None) -> List[Tuple[str, Any]]:
        """Get all keys and values that start with the given prefix.
        
        DSA-USED:
        - Trie: O(m + k) prefix matching where m is prefix length and k is number of results
        
        Args:
            prefix: Prefix string to match
            limit: Optional maximum number of results to return
        
        Returns:
            List of (key, value) tuples matching the prefix
        """
        results = []
        node = self._find_node(prefix)
        
        if not node:
            return results
        
        def _collect(node: TrieNode, current_prefix: str):
            if limit and len(results) >= limit:
                return
            
            if node.is_end:
                results.append((current_prefix, node.value))
            
            for char, child in sorted(node.children.items()):
                if limit and len(results) >= limit:
                    return
                _collect(child, current_prefix + char)
        
        _collect(node, prefix)
        return results
    
    def autocomplete(self, prefix: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions for a prefix.
        
        Args:
            prefix: Prefix string for autocomplete
            limit: Maximum number of suggestions (default: 10)
        
        Returns:
            List of key strings matching the prefix
        """
        matches = self.get_prefix_matches(prefix, limit)
        return [key for key, _ in matches]
    
    def match_pattern(self, pattern: str, wildcard: str = "*") -> List[Tuple[str, Any]]:
        """Find all keys matching a pattern with wildcards.
        
        DSA-USED:
        - Trie: Pattern matching with wildcard support using DFS traversal
        
        Args:
            pattern: Pattern string with wildcards
            wildcard: Wildcard character (default: "*")
        
        Returns:
            List of (key, value) tuples matching the pattern
        """
        results = []
        
        def _match(node: TrieNode, pattern_idx: int, current_key: str):
            if pattern_idx == len(pattern):
                if node.is_end:
                    results.append((current_key, node.value))
                return
            
            char = pattern[pattern_idx]
            
            if char == wildcard:
                for c, child in node.children.items():
                    _match(child, pattern_idx + 1, current_key + c)
            elif char in node.children:
                _match(node.children[char], pattern_idx + 1, current_key + char)
        
        _match(self._root, 0, "")
        return results
    
    def match_regex_simple(self, pattern: str) -> List[Tuple[str, Any]]:
        """Find all keys matching a simple regex pattern (supports . and *).
        
        DSA-USED:
        - Trie: Simple regex matching with . (any char) and * (zero or more) support
        
        Args:
            pattern: Regex pattern string
        
        Returns:
            List of (key, value) tuples matching the pattern
        """
        results = []
        
        def _match(node: TrieNode, pattern_idx: int, current_key: str):
            if pattern_idx == len(pattern):
                if node.is_end:
                    results.append((current_key, node.value))
                return
            
            char = pattern[pattern_idx]
            
            if char == ".":
                for c, child in node.children.items():
                    _match(child, pattern_idx + 1, current_key + c)
            elif pattern_idx + 1 < len(pattern) and pattern[pattern_idx + 1] == "*":
                _match(node, pattern_idx + 2, current_key)
                
                if char == ".":
                    for c, child in node.children.items():
                        _match(child, pattern_idx, current_key + c)
                elif char in node.children:
                    _match(node.children[char], pattern_idx, current_key + char)
            elif char in node.children:
                _match(node.children[char], pattern_idx + 1, current_key + char)
        
        _match(self._root, 0, "")
        return results
    
    def keys(self) -> Generator[str, None, None]:
        """Generate all keys in the trie.
        
        Yields:
            All keys in the trie
        """
        def _keys(node: TrieNode, prefix: str):
            if node.is_end:
                yield prefix
            for char, child in sorted(node.children.items()):
                yield from _keys(child, prefix + char)
        
        yield from _keys(self._root, "")
    
    def values(self) -> Generator[Any, None, None]:
        """Generate all values in the trie.
        
        Yields:
            All values in the trie
        """
        def _values(node: TrieNode):
            if node.is_end:
                yield node.value
            for child in node.children.values():
                yield from _values(child)
        
        yield from _values(self._root)
    
    def items(self) -> Generator[Tuple[str, Any], None, None]:
        """Generate all key-value pairs in the trie.
        
        Yields:
            Tuples of (key, value) pairs
        """
        def _items(node: TrieNode, prefix: str):
            if node.is_end:
                yield (prefix, node.value)
            for char, child in sorted(node.children.items()):
                yield from _items(child, prefix + char)
        
        yield from _items(self._root, "")
    
    def clear(self):
        """Remove all keys from the trie."""
        self._root = TrieNode()
        self._size = 0
    
    def get_longest_prefix(self, text: str) -> Optional[Tuple[str, Any]]:
        """Find the longest key that is a prefix of the given text.
        
        Args:
            text: Text to find longest prefix match for
        
        Returns:
            Tuple of (key, value) for the longest matching prefix, or None if no match
        """
        node = self._root
        last_match = None
        current_prefix = ""
        
        for char in text:
            if char not in node.children:
                break
            
            node = node.children[char]
            current_prefix += char
            
            if node.is_end:
                last_match = (current_prefix, node.value)
        
        return last_match
    
    def find_all_in_text(self, text: str) -> List[Tuple[int, str, Any]]:
        """Find all keys that appear as substrings in the given text.
        
        DSA-USED:
        - Trie: O(n*m) substring matching where n is text length and m is average key length
        
        Args:
            text: Text to search in
        
        Returns:
            List of (start_index, matched_key, value) tuples
        """
        results = []
        
        for i in range(len(text)):
            node = self._root
            j = i
            
            while j < len(text) and text[j] in node.children:
                node = node.children[text[j]]
                j += 1
                
                if node.is_end:
                    results.append((i, text[i:j], node.value))
        
        return results
    
    def to_dict(self) -> dict:
        """Convert the trie to a standard Python dictionary.
        
        Returns:
            Dictionary representation of the trie
        """
        return dict(self.items())
    
    @classmethod
    def from_dict(cls, d: dict) -> "Trie":
        """Create a Trie from a dictionary.
        
        Args:
            d: Dictionary to convert
        
        Returns:
            New Trie instance with keys and values from the dictionary
        """
        trie = cls()
        for key, value in d.items():
            trie.insert(key, value)
        return trie
    
    @classmethod
    def from_list(cls, keys: List[str]) -> "Trie":
        """Create a Trie from a list of keys.
        
        Args:
            keys: List of string keys to add
        
        Returns:
            New Trie instance containing the keys
        """
        trie = cls()
        for key in keys:
            trie.insert(key)
        return trie


