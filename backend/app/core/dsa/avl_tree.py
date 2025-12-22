"""AVL Tree (Self-Balancing Binary Search Tree) implementation.

This module implements an AVL Tree, a self-balancing binary search tree that maintains
O(log n) time complexity for insert, search, and delete operations. The tree automatically
rebalances itself after each insertion or deletion to maintain height balance.

DSA Concept: AVL Tree (Self-Balancing BST)
- Automatic balancing on insert/delete operations
- Range queries with O(log n + k) complexity
- Floor and ceiling operations for nearest value lookups
- In-order, pre-order, and post-order traversals
- O(log n) time complexity for all operations
"""

from typing import Any, Optional, List, Tuple, Generator, Callable
from dataclasses import dataclass
import json


@dataclass
class AVLNode:
    key: Any
    value: Any
    height: int = 1
    left: Optional["AVLNode"] = None
    right: Optional["AVLNode"] = None
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "height": self.height,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None
        }


class AVLTree:
    
    def __init__(self, compare: Callable[[Any, Any], int] = None):
        self.root: Optional[AVLNode] = None
        self._size = 0
        self._compare = compare or self._default_compare
    
    @staticmethod
    def _default_compare(a: Any, b: Any) -> int:
        if a < b:
            return -1
        elif a > b:
            return 1
        return 0
    
    def __len__(self) -> int:
        return self._size
    
    def __contains__(self, key: Any) -> bool:
        return self.search(key) is not None
    
    def __iter__(self) -> Generator[Tuple[Any, Any], None, None]:
        
        yield from self.inorder()
    
    def _height(self, node: Optional[AVLNode]) -> int:
        """Get the height of a node.
        
        Args:
            node: AVLNode to get height for
        
        Returns:
            Height of the node, or 0 if node is None
        """
        return node.height if node else 0
    
    def _balance_factor(self, node: Optional[AVLNode]) -> int:
        """Calculate the balance factor of a node (left height - right height).
        
        DSA-USED:
        - AVLTree: Balance factor calculation for tree balancing
        
        Args:
            node: AVLNode to calculate balance factor for
        
        Returns:
            Balance factor (positive = left-heavy, negative = right-heavy, 0 = balanced)
        """
        if not node:
            return 0
        return self._height(node.left) - self._height(node.right)
    
    def _update_height(self, node: AVLNode):
        """Update the height of a node based on its children.
        
        Args:
            node: AVLNode to update height for
        """
        node.height = 1 + max(self._height(node.left), self._height(node.right))
    
    def _rotate_right(self, y: AVLNode) -> AVLNode:
        """Perform a right rotation to rebalance the tree.
        
        DSA-USED:
        - AVLTree: Right rotation operation for tree balancing
        
        Args:
            y: Node to rotate around
        
        Returns:
            New root node after rotation
        """
        x = y.left
        T2 = x.right
        
        x.right = y
        y.left = T2
        
        self._update_height(y)
        self._update_height(x)
        
        return x
    
    def _rotate_left(self, x: AVLNode) -> AVLNode:
        """Perform a left rotation to rebalance the tree.
        
        DSA-USED:
        - AVLTree: Left rotation operation for tree balancing
        
        Args:
            x: Node to rotate around
        
        Returns:
            New root node after rotation
        """
        y = x.right
        T2 = y.left
        
        y.left = x
        x.right = T2
        
        self._update_height(x)
        self._update_height(y)
        
        return y
    
    def _rebalance(self, node: AVLNode, key: Any) -> AVLNode:
        """Rebalance the tree after insertion or deletion.
        
        DSA-USED:
        - AVLTree: Tree rebalancing using rotations to maintain AVL property
        
        Args:
            node: Node to rebalance
            key: Key that was inserted/deleted (used to determine rotation direction)
        
        Returns:
            Rebalanced node
        """
        self._update_height(node)
        
        balance = self._balance_factor(node)
        
        if balance > 1 and self._compare(key, node.left.key) < 0:
            return self._rotate_right(node)
        
        if balance < -1 and self._compare(key, node.right.key) > 0:
            return self._rotate_left(node)
        
        if balance > 1 and self._compare(key, node.left.key) > 0:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        
        if balance < -1 and self._compare(key, node.right.key) < 0:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        
        return node
    
    def insert(self, key: Any, value: Any = None) -> bool:
        """Insert a key-value pair with automatic rebalancing.
        
        DSA-USED:
        - AVLTree: Self-balancing BST insertion with rotation operations
        
        Args:
            key: Key to insert
            value: Value to associate (defaults to key if None)
        
        Returns:
            True if new key was inserted, False if existing key was updated
        """
        if value is None:
            value = key
        
        def _insert(node: Optional[AVLNode], key: Any, value: Any) -> Tuple[AVLNode, bool]:
            if not node:
                self._size += 1
                return AVLNode(key=key, value=value), True  # DSA-USED: AVLTree
            
            cmp = self._compare(key, node.key)  # DSA-USED: AVLTree
            
            if cmp < 0:
                node.left, inserted = _insert(node.left, key, value)  # DSA-USED: AVLTree
            elif cmp > 0:
                node.right, inserted = _insert(node.right, key, value)  # DSA-USED: AVLTree
            else:
                node.value = value
                return node, False
            
            if inserted:
                node = self._rebalance(node, key)  # DSA-USED: AVLTree
            
            return node, inserted
        
        self.root, inserted = _insert(self.root, key, value)  # DSA-USED: AVLTree
        return inserted
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for a key in the tree.
        
        DSA-USED:
        - AVLTree: O(log n) binary search in balanced tree
        
        Args:
            key: Key to search for
        
        Returns:
            Associated value if found, None otherwise
        """
        node = self.root  # DSA-USED: AVLTree
        
        while node:  # DSA-USED: AVLTree
            cmp = self._compare(key, node.key)  # DSA-USED: AVLTree
            
            if cmp < 0:
                node = node.left  # DSA-USED: AVLTree
            elif cmp > 0:
                node = node.right  # DSA-USED: AVLTree
            else:
                return node.value
        
        return None
    
    def delete(self, key: Any) -> bool:
        """Delete a key from the tree with automatic rebalancing.
        
        DSA-USED:
        - AVLTree: Self-balancing BST deletion with rotation operations
        
        Args:
            key: Key to delete
        
        Returns:
            True if key was found and deleted, False otherwise
        """
        def _min_value_node(node: AVLNode) -> AVLNode:
            current = node
            while current.left:
                current = current.left
            return current
        
        def _delete(node: Optional[AVLNode], key: Any) -> Tuple[Optional[AVLNode], bool]:
            if not node:
                return None, False
            
            cmp = self._compare(key, node.key)
            
            if cmp < 0:
                node.left, deleted = _delete(node.left, key)
            elif cmp > 0:
                node.right, deleted = _delete(node.right, key)
            else:
                deleted = True
                self._size -= 1
                
                if not node.left:
                    return node.right, deleted
                elif not node.right:
                    return node.left, deleted
                
                successor = _min_value_node(node.right)
                node.key = successor.key
                node.value = successor.value
                self._size += 1
                node.right, _ = _delete(node.right, successor.key)
            
            if not deleted:
                return node, deleted
            
            self._update_height(node)
            
            balance = self._balance_factor(node)
            
            if balance > 1 and self._balance_factor(node.left) >= 0:
                return self._rotate_right(node), deleted
            
            if balance > 1 and self._balance_factor(node.left) < 0:
                node.left = self._rotate_left(node.left)
                return self._rotate_right(node), deleted
            
            if balance < -1 and self._balance_factor(node.right) <= 0:
                return self._rotate_left(node), deleted
            
            if balance < -1 and self._balance_factor(node.right) > 0:
                node.right = self._rotate_right(node.right)
                return self._rotate_left(node), deleted
            
            return node, deleted
        
        self.root, deleted = _delete(self.root, key)
        return deleted
    
    def range_query(self, low: Any, high: Any) -> List[Tuple[Any, Any]]:
        """Query all key-value pairs in the range [low, high].
        
        DSA-USED:
        - AVLTree: O(log n + k) range query using in-order traversal
        
        Args:
            low: Lower bound (inclusive)
            high: Upper bound (inclusive)
        
        Returns:
            List of (key, value) tuples in the specified range
        """
        result = []
        
        def _range(node: Optional[AVLNode]):
            if not node:
                return
            
            if self._compare(node.key, low) > 0:  # DSA-USED: AVLTree
                _range(node.left)  # DSA-USED: AVLTree
            
            if self._compare(node.key, low) >= 0 and self._compare(node.key, high) <= 0:  # DSA-USED: AVLTree
                result.append((node.key, node.value))
            
            if self._compare(node.key, high) < 0:  # DSA-USED: AVLTree
                _range(node.right)  # DSA-USED: AVLTree
        
        _range(self.root)  # DSA-USED: AVLTree
        return result
    
    def floor(self, key: Any) -> Optional[Tuple[Any, Any]]:
        """Find the largest key less than or equal to the given key.
        
        Args:
            key: Key to find floor for
        
        Returns:
            Tuple of (key, value) for the floor, or None if no floor exists
        """
        result = None
        node = self.root
        
        while node:
            cmp = self._compare(key, node.key)
            
            if cmp == 0:
                return (node.key, node.value)
            elif cmp < 0:
                node = node.left
            else:
                result = (node.key, node.value)
                node = node.right
        
        return result
    
    def ceiling(self, key: Any) -> Optional[Tuple[Any, Any]]:
        """Find the smallest key greater than or equal to the given key.
        
        Args:
            key: Key to find ceiling for
        
        Returns:
            Tuple of (key, value) for the ceiling, or None if no ceiling exists
        """
        result = None
        node = self.root
        
        while node:
            cmp = self._compare(key, node.key)
            
            if cmp == 0:
                return (node.key, node.value)
            elif cmp > 0:
                node = node.right
            else:
                result = (node.key, node.value)
                node = node.left
        
        return result
    
    def inorder(self) -> Generator[Tuple[Any, Any], None, None]:
        """Generate key-value pairs in in-order traversal (sorted order).
        
        Yields:
            Tuples of (key, value) in sorted order
        """
        def _inorder(node: Optional[AVLNode]):
            if node:
                yield from _inorder(node.left)
                yield (node.key, node.value)
                yield from _inorder(node.right)
        
        yield from _inorder(self.root)
    
    def preorder(self) -> Generator[Tuple[Any, Any], None, None]:
        """Generate key-value pairs in pre-order traversal.
        
        Yields:
            Tuples of (key, value) in pre-order
        """
        def _preorder(node: Optional[AVLNode]):
            if node:
                yield (node.key, node.value)
                yield from _preorder(node.left)
                yield from _preorder(node.right)
        
        yield from _preorder(self.root)
    
    def postorder(self) -> Generator[Tuple[Any, Any], None, None]:
        """Generate key-value pairs in post-order traversal.
        
        Yields:
            Tuples of (key, value) in post-order
        """
        def _postorder(node: Optional[AVLNode]):
            if node:
                yield from _postorder(node.left)
                yield from _postorder(node.right)
                yield (node.key, node.value)
        
        yield from _postorder(self.root)
    
    def level_order(self) -> Generator[Tuple[Any, Any], None, None]:
        if not self.root:
            return
        
        from collections import deque
        queue = deque([self.root])
        
        while queue:
            node = queue.popleft()
            yield (node.key, node.value)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
    
    def minimum(self) -> Optional[Tuple[Any, Any]]:
        """Get the minimum key-value pair in the tree.
        
        Returns:
            Tuple of (key, value) for the minimum key, or None if tree is empty
        """
        if not self.root:
            return None
        
        node = self.root
        while node.left:
            node = node.left
        
        return (node.key, node.value)
    
    def maximum(self) -> Optional[Tuple[Any, Any]]:
        """Get the maximum key-value pair in the tree.
        
        Returns:
            Tuple of (key, value) for the maximum key, or None if tree is empty
        """
        if not self.root:
            return None
        
        node = self.root
        while node.right:
            node = node.right
        
        return (node.key, node.value)
    
    def clear(self):
        """Remove all keys from the tree."""
        self.root = None
        self._size = 0
    
    def height(self) -> int:
        return self._height(self.root)
    
    def is_balanced(self) -> bool:
        def _check(node: Optional[AVLNode]) -> Tuple[bool, int]:
            if not node:
                return True, 0
            
            left_balanced, left_height = _check(node.left)
            right_balanced, right_height = _check(node.right)
            
            balanced = (left_balanced and right_balanced and 
                       abs(left_height - right_height) <= 1)
            height = 1 + max(left_height, right_height)
            
            return balanced, height
        
        balanced, _ = _check(self.root)
        return balanced
    
    def to_dict(self) -> dict:
        """Convert the tree to a dictionary representation.
        
        Returns:
            Dictionary containing tree structure
        """
        return {
            "root": self.root.to_dict() if self.root else None,
            "size": self._size
        }
    
    def to_list(self) -> List[Tuple[Any, Any]]:
        return list(self.inorder())
    
    @classmethod
    def from_list(cls, items: List[Tuple[Any, Any]]) -> "AVLTree":
        """Create an AVLTree from a list of key-value pairs.
        
        Args:
            items: List of (key, value) tuples
        
        Returns:
            New AVLTree instance
        """
        tree = cls()
        for key, value in items:
            tree.insert(key, value)
        return tree


