"""
Custom Trie (Prefix Tree) Implementation

Efficient prefix-based string storage and retrieval.

Used for:
- Domain name matching
- Keyword pattern search
- Username/password pattern detection
- Autocomplete suggestions
"""

from typing import Any, Optional, List, Dict, Generator, Tuple
from dataclasses import dataclass, field


@dataclass
class TrieNode:
    """Node in the Trie."""
    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    is_end: bool = False
    value: Any = None
    count: int = 0  # Number of words passing through this node


class Trie:
    """
    Trie (Prefix Tree) Implementation.
    
    Features:
    - O(m) insert, search, delete where m = key length
    - Prefix matching and autocomplete
    - Pattern matching with wildcards
    - Count of words with given prefix
    """
    
    def __init__(self):
        """Initialize empty Trie."""
        self._root = TrieNode()
        self._size = 0
    
    def __len__(self) -> int:
        return self._size
    
    def __contains__(self, key: str) -> bool:
        return self.search(key) is not None
    
    def __iter__(self) -> Generator[str, None, None]:
        """Iterate over all keys."""
        yield from self.keys()
    
    # ==================== Core Operations ====================
    
    def insert(self, key: str, value: Any = None) -> bool:
        """Insert a key-value pair.
        
        Args:
            key: The key to insert
            value: Optional value (defaults to True)
            
        Returns:
            True if new key, False if updated existing
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
        """Search for a key.
        
        Args:
            key: The key to search for
            
        Returns:
            The value if found, None otherwise
        """
        node = self._find_node(key)
        
        if node and node.is_end:
            return node.value
        return None
    
    def delete(self, key: str) -> bool:
        """Delete a key.
        
        Args:
            key: The key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        if not key:
            return False
        
        def _delete(node: TrieNode, key: str, depth: int) -> Tuple[bool, bool]:
            """Returns (key_found, should_delete_node)"""
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
        """Find the node corresponding to a prefix."""
        node = self._root
        
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        
        return node
    
    # ==================== Prefix Operations ====================
    
    def starts_with(self, prefix: str) -> bool:
        """Check if any key starts with the given prefix.
        
        Args:
            prefix: The prefix to check
            
        Returns:
            True if any key has this prefix
        """
        return self._find_node(prefix) is not None
    
    def count_prefix(self, prefix: str) -> int:
        """Count keys with given prefix.
        
        Args:
            prefix: The prefix to count
            
        Returns:
            Number of keys with this prefix
        """
        node = self._find_node(prefix)
        return node.count if node else 0
    
    def get_prefix_matches(self, prefix: str, limit: int = None) -> List[Tuple[str, Any]]:
        """Get all keys with given prefix.
        
        Args:
            prefix: The prefix to match
            limit: Optional maximum number of results
            
        Returns:
            List of (key, value) tuples
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
        """Get autocomplete suggestions for prefix.
        
        Args:
            prefix: The prefix to complete
            limit: Maximum number of suggestions
            
        Returns:
            List of complete keys
        """
        matches = self.get_prefix_matches(prefix, limit)
        return [key for key, _ in matches]
    
    # ==================== Pattern Matching ====================
    
    def match_pattern(self, pattern: str, wildcard: str = "*") -> List[Tuple[str, Any]]:
        """Match keys against pattern with wildcards.
        
        Args:
            pattern: Pattern with wildcards (e.g., "a*c" matches "abc", "adc")
            wildcard: Wildcard character (default "*")
            
        Returns:
            List of (key, value) tuples matching pattern
        """
        results = []
        
        def _match(node: TrieNode, pattern_idx: int, current_key: str):
            if pattern_idx == len(pattern):
                if node.is_end:
                    results.append((current_key, node.value))
                return
            
            char = pattern[pattern_idx]
            
            if char == wildcard:
                # Wildcard matches any single character
                for c, child in node.children.items():
                    _match(child, pattern_idx + 1, current_key + c)
            elif char in node.children:
                _match(node.children[char], pattern_idx + 1, current_key + char)
        
        _match(self._root, 0, "")
        return results
    
    def match_regex_simple(self, pattern: str) -> List[Tuple[str, Any]]:
        """Match keys against simple regex pattern.
        
        Supports:
        - . (any single character)
        - * (zero or more of previous)
        
        Args:
            pattern: Simple regex pattern
            
        Returns:
            List of matching (key, value) tuples
        """
        results = []
        
        def _match(node: TrieNode, pattern_idx: int, current_key: str):
            if pattern_idx == len(pattern):
                if node.is_end:
                    results.append((current_key, node.value))
                return
            
            char = pattern[pattern_idx]
            
            if char == ".":
                # Match any single character
                for c, child in node.children.items():
                    _match(child, pattern_idx + 1, current_key + c)
            elif pattern_idx + 1 < len(pattern) and pattern[pattern_idx + 1] == "*":
                # Zero or more of current character
                _match(node, pattern_idx + 2, current_key)  # Zero occurrences
                
                if char == ".":
                    for c, child in node.children.items():
                        _match(child, pattern_idx, current_key + c)
                elif char in node.children:
                    _match(node.children[char], pattern_idx, current_key + char)
            elif char in node.children:
                _match(node.children[char], pattern_idx + 1, current_key + char)
        
        _match(self._root, 0, "")
        return results
    
    # ==================== Iteration ====================
    
    def keys(self) -> Generator[str, None, None]:
        """Iterate over all keys."""
        def _keys(node: TrieNode, prefix: str):
            if node.is_end:
                yield prefix
            for char, child in sorted(node.children.items()):
                yield from _keys(child, prefix + char)
        
        yield from _keys(self._root, "")
    
    def values(self) -> Generator[Any, None, None]:
        """Iterate over all values."""
        def _values(node: TrieNode):
            if node.is_end:
                yield node.value
            for child in node.children.values():
                yield from _values(child)
        
        yield from _values(self._root)
    
    def items(self) -> Generator[Tuple[str, Any], None, None]:
        """Iterate over all (key, value) pairs."""
        def _items(node: TrieNode, prefix: str):
            if node.is_end:
                yield (prefix, node.value)
            for char, child in sorted(node.children.items()):
                yield from _items(child, prefix + char)
        
        yield from _items(self._root, "")
    
    # ==================== Utility ====================
    
    def clear(self):
        """Remove all keys."""
        self._root = TrieNode()
        self._size = 0
    
    def get_longest_prefix(self, text: str) -> Optional[Tuple[str, Any]]:
        """Find longest key that is a prefix of text.
        
        Args:
            text: Text to find prefix in
            
        Returns:
            (key, value) of longest matching prefix, or None
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
        """Find all keys that appear in text.
        
        Args:
            text: Text to search
            
        Returns:
            List of (position, key, value) tuples
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
        """Convert to dictionary."""
        return dict(self.items())
    
    @classmethod
    def from_dict(cls, d: dict) -> "Trie":
        """Create Trie from dictionary."""
        trie = cls()
        for key, value in d.items():
            trie.insert(key, value)
        return trie
    
    @classmethod
    def from_list(cls, keys: List[str]) -> "Trie":
        """Create Trie from list of keys."""
        trie = cls()
        for key in keys:
            trie.insert(key)
        return trie


