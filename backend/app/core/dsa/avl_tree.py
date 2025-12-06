"""
Custom AVL Tree Implementation

Self-balancing Binary Search Tree for efficient IOC lookups and indexing.

Used for:
- IOC (Indicators of Compromise) indexing
- Fast entity lookups by various attributes
- Range queries on timestamps, severity scores
"""

from typing import Any, Optional, List, Tuple, Generator, Callable
from dataclasses import dataclass
import json


@dataclass
class AVLNode:
    """Node in AVL Tree."""
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
    """
    AVL Tree - Self-balancing Binary Search Tree.
    
    Properties:
    - Height difference between left and right subtrees is at most 1
    - All BST operations are O(log n)
    - Automatic rebalancing on insert/delete
    
    Features:
    - Insert, search, delete in O(log n)
    - Range queries
    - In-order, pre-order, post-order traversals
    - Minimum, maximum lookups
    - Serialization support
    """
    
    def __init__(self, compare: Callable[[Any, Any], int] = None):
        """Initialize AVL Tree.
        
        Args:
            compare: Optional comparison function. Should return:
                     - negative if a < b
                     - zero if a == b
                     - positive if a > b
        """
        self.root: Optional[AVLNode] = None
        self._size = 0
        self._compare = compare or self._default_compare
    
    @staticmethod
    def _default_compare(a: Any, b: Any) -> int:
        """Default comparison function."""
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
        """Iterate over tree in-order (sorted order)."""
        yield from self.inorder()
    
    # ==================== Height and Balance ====================
    
    def _height(self, node: Optional[AVLNode]) -> int:
        """Get height of a node."""
        return node.height if node else 0
    
    def _balance_factor(self, node: Optional[AVLNode]) -> int:
        """Get balance factor of a node."""
        if not node:
            return 0
        return self._height(node.left) - self._height(node.right)
    
    def _update_height(self, node: AVLNode):
        """Update height of a node."""
        node.height = 1 + max(self._height(node.left), self._height(node.right))
    
    # ==================== Rotations ====================
    
    def _rotate_right(self, y: AVLNode) -> AVLNode:
        """Perform right rotation.
        
              y                x
             / \              / \
            x   T3    -->   T1   y
           / \                  / \
          T1  T2              T2  T3
        """
        x = y.left
        T2 = x.right
        
        # Perform rotation
        x.right = y
        y.left = T2
        
        # Update heights
        self._update_height(y)
        self._update_height(x)
        
        return x
    
    def _rotate_left(self, x: AVLNode) -> AVLNode:
        """Perform left rotation.
        
            x                  y
           / \                / \
          T1  y      -->     x   T3
             / \            / \
            T2  T3        T1  T2
        """
        y = x.right
        T2 = y.left
        
        # Perform rotation
        y.left = x
        x.right = T2
        
        # Update heights
        self._update_height(x)
        self._update_height(y)
        
        return y
    
    def _rebalance(self, node: AVLNode, key: Any) -> AVLNode:
        """Rebalance the tree after insertion."""
        # Update height
        self._update_height(node)
        
        # Get balance factor
        balance = self._balance_factor(node)
        
        # Left Left Case
        if balance > 1 and self._compare(key, node.left.key) < 0:
            return self._rotate_right(node)
        
        # Right Right Case
        if balance < -1 and self._compare(key, node.right.key) > 0:
            return self._rotate_left(node)
        
        # Left Right Case
        if balance > 1 and self._compare(key, node.left.key) > 0:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        
        # Right Left Case
        if balance < -1 and self._compare(key, node.right.key) < 0:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        
        return node
    
    # ==================== Core Operations ====================
    
    def insert(self, key: Any, value: Any = None) -> bool:
        """Insert a key-value pair into the tree.
        
        Args:
            key: The key to insert
            value: The value associated with the key (defaults to key)
            
        Returns:
            True if inserted, False if key already exists
        """
        if value is None:
            value = key
        
        def _insert(node: Optional[AVLNode], key: Any, value: Any) -> Tuple[AVLNode, bool]:
            # Base case: empty position found
            if not node:
                self._size += 1
                return AVLNode(key=key, value=value), True
            
            cmp = self._compare(key, node.key)
            
            if cmp < 0:
                node.left, inserted = _insert(node.left, key, value)
            elif cmp > 0:
                node.right, inserted = _insert(node.right, key, value)
            else:
                # Key already exists, update value
                node.value = value
                return node, False
            
            if inserted:
                node = self._rebalance(node, key)
            
            return node, inserted
        
        self.root, inserted = _insert(self.root, key, value)
        return inserted
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for a key in the tree.
        
        Args:
            key: The key to search for
            
        Returns:
            The value if found, None otherwise
        """
        node = self.root
        
        while node:
            cmp = self._compare(key, node.key)
            
            if cmp < 0:
                node = node.left
            elif cmp > 0:
                node = node.right
            else:
                return node.value
        
        return None
    
    def delete(self, key: Any) -> bool:
        """Delete a key from the tree.
        
        Args:
            key: The key to delete
            
        Returns:
            True if deleted, False if key not found
        """
        def _min_value_node(node: AVLNode) -> AVLNode:
            """Find the node with minimum key in a subtree."""
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
                # Node to delete found
                deleted = True
                self._size -= 1
                
                # Node with only one child or no child
                if not node.left:
                    return node.right, deleted
                elif not node.right:
                    return node.left, deleted
                
                # Node with two children
                # Get inorder successor (smallest in right subtree)
                successor = _min_value_node(node.right)
                node.key = successor.key
                node.value = successor.value
                self._size += 1  # Compensate for the recursive delete
                node.right, _ = _delete(node.right, successor.key)
            
            if not deleted:
                return node, deleted
            
            # Update height
            self._update_height(node)
            
            # Rebalance
            balance = self._balance_factor(node)
            
            # Left Left Case
            if balance > 1 and self._balance_factor(node.left) >= 0:
                return self._rotate_right(node), deleted
            
            # Left Right Case
            if balance > 1 and self._balance_factor(node.left) < 0:
                node.left = self._rotate_left(node.left)
                return self._rotate_right(node), deleted
            
            # Right Right Case
            if balance < -1 and self._balance_factor(node.right) <= 0:
                return self._rotate_left(node), deleted
            
            # Right Left Case
            if balance < -1 and self._balance_factor(node.right) > 0:
                node.right = self._rotate_right(node.right)
                return self._rotate_left(node), deleted
            
            return node, deleted
        
        self.root, deleted = _delete(self.root, key)
        return deleted
    
    # ==================== Range Operations ====================
    
    def range_query(self, low: Any, high: Any) -> List[Tuple[Any, Any]]:
        """Get all key-value pairs in range [low, high].
        
        Args:
            low: Lower bound (inclusive)
            high: Upper bound (inclusive)
            
        Returns:
            List of (key, value) tuples in sorted order
        """
        result = []
        
        def _range(node: Optional[AVLNode]):
            if not node:
                return
            
            # If node's key is greater than low, search left subtree
            if self._compare(node.key, low) > 0:
                _range(node.left)
            
            # If node's key is in range, include it
            if self._compare(node.key, low) >= 0 and self._compare(node.key, high) <= 0:
                result.append((node.key, node.value))
            
            # If node's key is less than high, search right subtree
            if self._compare(node.key, high) < 0:
                _range(node.right)
        
        _range(self.root)
        return result
    
    def floor(self, key: Any) -> Optional[Tuple[Any, Any]]:
        """Find the largest key less than or equal to given key."""
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
        """Find the smallest key greater than or equal to given key."""
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
    
    # ==================== Traversals ====================
    
    def inorder(self) -> Generator[Tuple[Any, Any], None, None]:
        """In-order traversal (sorted order)."""
        def _inorder(node: Optional[AVLNode]):
            if node:
                yield from _inorder(node.left)
                yield (node.key, node.value)
                yield from _inorder(node.right)
        
        yield from _inorder(self.root)
    
    def preorder(self) -> Generator[Tuple[Any, Any], None, None]:
        """Pre-order traversal."""
        def _preorder(node: Optional[AVLNode]):
            if node:
                yield (node.key, node.value)
                yield from _preorder(node.left)
                yield from _preorder(node.right)
        
        yield from _preorder(self.root)
    
    def postorder(self) -> Generator[Tuple[Any, Any], None, None]:
        """Post-order traversal."""
        def _postorder(node: Optional[AVLNode]):
            if node:
                yield from _postorder(node.left)
                yield from _postorder(node.right)
                yield (node.key, node.value)
        
        yield from _postorder(self.root)
    
    def level_order(self) -> Generator[Tuple[Any, Any], None, None]:
        """Level-order (BFS) traversal."""
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
    
    # ==================== Min/Max ====================
    
    def minimum(self) -> Optional[Tuple[Any, Any]]:
        """Get the minimum key-value pair."""
        if not self.root:
            return None
        
        node = self.root
        while node.left:
            node = node.left
        
        return (node.key, node.value)
    
    def maximum(self) -> Optional[Tuple[Any, Any]]:
        """Get the maximum key-value pair."""
        if not self.root:
            return None
        
        node = self.root
        while node.right:
            node = node.right
        
        return (node.key, node.value)
    
    # ==================== Utility ====================
    
    def clear(self):
        """Clear the tree."""
        self.root = None
        self._size = 0
    
    def height(self) -> int:
        """Get the height of the tree."""
        return self._height(self.root)
    
    def is_balanced(self) -> bool:
        """Check if the tree is balanced (for testing)."""
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
    
    # ==================== Serialization ====================
    
    def to_dict(self) -> dict:
        """Serialize tree to dictionary."""
        return {
            "root": self.root.to_dict() if self.root else None,
            "size": self._size
        }
    
    def to_list(self) -> List[Tuple[Any, Any]]:
        """Convert tree to sorted list of (key, value) tuples."""
        return list(self.inorder())
    
    @classmethod
    def from_list(cls, items: List[Tuple[Any, Any]]) -> "AVLTree":
        """Build tree from list of (key, value) tuples."""
        tree = cls()
        for key, value in items:
            tree.insert(key, value)
        return tree


