"""B-Tree implementation.

This module implements a B-Tree data structure optimized for disk-based storage.
All leaves are at the same level, making it ideal for large dataset indexing
and efficient range queries.

DSA Concept: B-Tree
- Disk-optimized structure with configurable branching factor
- Range queries with O(log n) complexity
- All leaves at same level
- O(log n) insert, search, and delete operations
- Ideal for persistent index storage
"""

from typing import Any, Optional, List, Tuple, Generator
from dataclasses import dataclass, field
import json


@dataclass
class BTreeNode:
    keys: List[Any] = field(default_factory=list)
    values: List[Any] = field(default_factory=list)
    children: List[Optional["BTreeNode"]] = field(default_factory=list)
    is_leaf: bool = True
    
    def to_dict(self) -> dict:
        return {
            "keys": self.keys,
            "values": self.values,
            "children": [c.to_dict() if c else None for c in self.children],
            "is_leaf": self.is_leaf
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BTreeNode":
        node = cls(
            keys=data["keys"],
            values=data["values"],
            is_leaf=data["is_leaf"]
        )
        node.children = [
            cls.from_dict(c) if c else None 
            for c in data.get("children", [])
        ]
        return node


class BTree:
    
    def __init__(self, t: int = 3):
        if t < 2:
            raise ValueError("Minimum degree must be at least 2")
        
        self._t = t
        self._root = BTreeNode()
        self._size = 0
    
    def __len__(self) -> int:
        return self._size
    
    def __contains__(self, key: Any) -> bool:
        return self.search(key) is not None
    
    def __iter__(self) -> Generator[Tuple[Any, Any], None, None]:
        yield from self._inorder(self._root)
    
    def _inorder(self, node: BTreeNode) -> Generator[Tuple[Any, Any], None, None]:
        if node is None:
            return
        
        for i in range(len(node.keys)):
            if not node.is_leaf and i < len(node.children):
                yield from self._inorder(node.children[i])
            yield (node.keys[i], node.values[i])
        
        if not node.is_leaf and len(node.children) > len(node.keys):
            yield from self._inorder(node.children[len(node.keys)])
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for a key in the B-tree.
        
        DSA-USED:
        - BTree: O(log n) search in balanced multi-way tree
        
        Args:
            key: Key to search for
        
        Returns:
            Associated value if found, None otherwise
        """
        return self._search(self._root, key)
    
    def _search(self, node: BTreeNode, key: Any) -> Optional[Any]:
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        if i < len(node.keys) and key == node.keys[i]:
            return node.values[i]
        
        if node.is_leaf:
            return None
        
        return self._search(node.children[i], key)
    
    def insert(self, key: Any, value: Any = None) -> bool:
        if value is None:
            value = key
        
        existing = self.search(key)
        if existing is not None:
            self._update(self._root, key, value)
            return False
        
        root = self._root
        
        if len(root.keys) == 2 * self._t - 1:
            new_root = BTreeNode(is_leaf=False)
            new_root.children.append(self._root)
            self._split_child(new_root, 0)
            self._root = new_root
            self._insert_non_full(new_root, key, value)
        else:
            self._insert_non_full(root, key, value)
        
        self._size += 1
        return True
    
    def _update(self, node: BTreeNode, key: Any, value: Any):
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        if i < len(node.keys) and key == node.keys[i]:
            node.values[i] = value
            return
        
        if not node.is_leaf:
            self._update(node.children[i], key, value)
    
    def _split_child(self, parent: BTreeNode, index: int):
        t = self._t
        child = parent.children[index]
        
        new_node = BTreeNode(is_leaf=child.is_leaf)
        
        new_node.keys = child.keys[t:]
        new_node.values = child.values[t:]
        child.keys = child.keys[:t-1]
        child.values = child.values[:t-1]
        
        if not child.is_leaf:
            new_node.children = child.children[t:]
            child.children = child.children[:t]
        
        median_key = child.keys[-1] if len(child.keys) >= t else new_node.keys[0]
        median_value = child.values[-1] if len(child.values) >= t else new_node.values[0]
        
        if len(child.keys) >= t:
            median_key = child.keys.pop()
            median_value = child.values.pop()
        
        parent.keys.insert(index, median_key)
        parent.values.insert(index, median_value)
        parent.children.insert(index + 1, new_node)
    
    def _insert_non_full(self, node: BTreeNode, key: Any, value: Any):
        i = len(node.keys) - 1
        
        if node.is_leaf:
            node.keys.append(None)
            node.values.append(None)
            
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            
            node.keys[i + 1] = key
            node.values[i + 1] = value
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            if len(node.children[i].keys) == 2 * self._t - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.children[i], key, value)
    
    def delete(self, key: Any) -> bool:
        """Delete a key from the B-tree.
        
        DSA-USED:
        - BTree: O(log n) deletion with node merging and borrowing
        
        Args:
            key: Key to delete
        
        Returns:
            True if key was found and deleted, False otherwise
        """
        if key not in self:
            return False
        
        self._delete(self._root, key)
        
        if len(self._root.keys) == 0 and not self._root.is_leaf:
            self._root = self._root.children[0]
        
        self._size -= 1
        return True
    
    def _delete(self, node: BTreeNode, key: Any):
        t = self._t
        i = 0
        
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        if i < len(node.keys) and key == node.keys[i]:
            if node.is_leaf:
                node.keys.pop(i)
                node.values.pop(i)
            else:
                if len(node.children[i].keys) >= t:
                    pred_key, pred_val = self._get_predecessor(node.children[i])
                    node.keys[i] = pred_key
                    node.values[i] = pred_val
                    self._delete(node.children[i], pred_key)
                elif len(node.children[i + 1].keys) >= t:
                    succ_key, succ_val = self._get_successor(node.children[i + 1])
                    node.keys[i] = succ_key
                    node.values[i] = succ_val
                    self._delete(node.children[i + 1], succ_key)
                else:
                    self._merge(node, i)
                    self._delete(node.children[i], key)
        else:
            if node.is_leaf:
                return
            
            if len(node.children[i].keys) < t:
                self._fill(node, i)
            
            if i > len(node.keys):
                i -= 1
            
            self._delete(node.children[i], key)
    
    def _get_predecessor(self, node: BTreeNode) -> Tuple[Any, Any]:
        while not node.is_leaf:
            node = node.children[-1]
        return (node.keys[-1], node.values[-1])
    
    def _get_successor(self, node: BTreeNode) -> Tuple[Any, Any]:
        while not node.is_leaf:
            node = node.children[0]
        return (node.keys[0], node.values[0])
    
    def _fill(self, node: BTreeNode, i: int):
        t = self._t
        
        if i > 0 and len(node.children[i - 1].keys) >= t:
            self._borrow_from_prev(node, i)
        elif i < len(node.keys) and len(node.children[i + 1].keys) >= t:
            self._borrow_from_next(node, i)
        else:
            if i < len(node.keys):
                self._merge(node, i)
            else:
                self._merge(node, i - 1)
    
    def _borrow_from_prev(self, node: BTreeNode, i: int):
        child = node.children[i]
        sibling = node.children[i - 1]
        
        child.keys.insert(0, node.keys[i - 1])
        child.values.insert(0, node.values[i - 1])
        
        node.keys[i - 1] = sibling.keys.pop()
        node.values[i - 1] = sibling.values.pop()
        
        if not child.is_leaf:
            child.children.insert(0, sibling.children.pop())
    
    def _borrow_from_next(self, node: BTreeNode, i: int):
        child = node.children[i]
        sibling = node.children[i + 1]
        
        child.keys.append(node.keys[i])
        child.values.append(node.values[i])
        
        node.keys[i] = sibling.keys.pop(0)
        node.values[i] = sibling.values.pop(0)
        
        if not child.is_leaf:
            child.children.append(sibling.children.pop(0))
    
    def _merge(self, node: BTreeNode, i: int):
        child = node.children[i]
        sibling = node.children[i + 1]
        
        child.keys.append(node.keys.pop(i))
        child.values.append(node.values.pop(i))
        
        child.keys.extend(sibling.keys)
        child.values.extend(sibling.values)
        
        if not child.is_leaf:
            child.children.extend(sibling.children)
        
        node.children.pop(i + 1)
    
    def range_query(self, low: Any, high: Any) -> List[Tuple[Any, Any]]:
        results = []
        self._range_query(self._root, low, high, results)
        return results
    
    def _range_query(self, node: BTreeNode, low: Any, high: Any, results: list):
        i = 0
        
        while i < len(node.keys) and node.keys[i] < low:
            i += 1
        
        while i < len(node.keys) and node.keys[i] <= high:
            if not node.is_leaf and i < len(node.children):
                self._range_query(node.children[i], low, high, results)
            
            results.append((node.keys[i], node.values[i]))
            i += 1
        
        if not node.is_leaf and i < len(node.children):
            self._range_query(node.children[i], low, high, results)
    
    def minimum(self) -> Optional[Tuple[Any, Any]]:
        """Get the minimum key-value pair in the B-tree.
        
        Returns:
            Tuple of (key, value) for the minimum key, or None if tree is empty
        """
        if not self._root.keys:
            return None
        
        node = self._root
        while not node.is_leaf:
            node = node.children[0]
        
        return (node.keys[0], node.values[0])
    
    def maximum(self) -> Optional[Tuple[Any, Any]]:
        """Get the maximum key-value pair in the B-tree.
        
        Returns:
            Tuple of (key, value) for the maximum key, or None if tree is empty
        """
        if not self._root.keys:
            return None
        
        node = self._root
        while not node.is_leaf:
            node = node.children[-1]
        
        return (node.keys[-1], node.values[-1])
    
    def clear(self):
        """Remove all keys from the B-tree."""
        self._root = BTreeNode()
        self._size = 0
    
    def height(self) -> int:
        """Get the height of the B-tree.
        
        Returns:
            Height of the tree (number of levels)
        """
        h = 0
        node = self._root
        while not node.is_leaf:
            h += 1
            node = node.children[0]
        return h
    
    def to_dict(self) -> dict:
        """Convert the B-tree to a dictionary representation.
        
        Returns:
            Dictionary containing tree structure and properties
        """
        return {
            "t": self._t,
            "size": self._size,
            "root": self._root.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BTree":
        """Create a BTree from a dictionary.
        
        Args:
            data: Dictionary containing tree structure
        
        Returns:
            New BTree instance
        """
        tree = cls(t=data["t"])
        tree._size = data["size"]
        tree._root = BTreeNode.from_dict(data["root"])
        return tree
    
    def to_list(self) -> List[Tuple[Any, Any]]:
        """Convert the B-tree to a list in sorted order.
        
        Returns:
            List of (key, value) tuples in sorted order
        """
        return list(self)


