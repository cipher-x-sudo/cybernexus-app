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
        """Iterate over tree in-order (sorted order)."""
        yield from self.inorder()
    
    def _height(self, node: Optional[AVLNode]) -> int:
        """Get height of a node."""
        return node.height if node else 0
    
    def _balance_factor(self, node: Optional[AVLNode]) -> int:
        """Get balance factor of a node."""
        if not node:
            return 0
        return self._height(node.left) - self._height(node.right)
    
    def _update_height(self, node: AVLNode):
        node.height = 1 + max(self._height(node.left), self._height(node.right))
    
    def _rotate_right(self, y: AVLNode) -> AVLNode:
        x = y.left
        T2 = x.right
        
        x.right = y
        y.left = T2
        
        self._update_height(y)
        self._update_height(x)
        
        return x
    
    def _rotate_left(self, x: AVLNode) -> AVLNode:
        y = x.right
        T2 = y.left
        
        y.left = x
        x.right = T2
        
        self._update_height(x)
        self._update_height(y)
        
        return y
    
    def _rebalance(self, node: AVLNode, key: Any) -> AVLNode:
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
        if value is None:
            value = key
        
        def _insert(node: Optional[AVLNode], key: Any, value: Any) -> Tuple[AVLNode, bool]:
            if not node:
                self._size += 1
                return AVLNode(key=key, value=value), True
            
            cmp = self._compare(key, node.key)
            
            if cmp < 0:
                node.left, inserted = _insert(node.left, key, value)
            elif cmp > 0:
                node.right, inserted = _insert(node.right, key, value)
            else:
                node.value = value
                return node, False
            
            if inserted:
                node = self._rebalance(node, key)
            
            return node, inserted
        
        self.root, inserted = _insert(self.root, key, value)
        return inserted
    
    def search(self, key: Any) -> Optional[Any]:
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
        result = []
        
        def _range(node: Optional[AVLNode]):
            if not node:
                return
            
            if self._compare(node.key, low) > 0:
                _range(node.left)
            
            if self._compare(node.key, low) >= 0 and self._compare(node.key, high) <= 0:
                result.append((node.key, node.value))
            
            if self._compare(node.key, high) < 0:
                _range(node.right)
        
        _range(self.root)
        return result
    
    def floor(self, key: Any) -> Optional[Tuple[Any, Any]]:
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
        def _inorder(node: Optional[AVLNode]):
            if node:
                yield from _inorder(node.left)
                yield (node.key, node.value)
                yield from _inorder(node.right)
        
        yield from _inorder(self.root)
    
    def preorder(self) -> Generator[Tuple[Any, Any], None, None]:
        def _preorder(node: Optional[AVLNode]):
            if node:
                yield (node.key, node.value)
                yield from _preorder(node.left)
                yield from _preorder(node.right)
        
        yield from _preorder(self.root)
    
    def postorder(self) -> Generator[Tuple[Any, Any], None, None]:
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
        if not self.root:
            return None
        
        node = self.root
        while node.left:
            node = node.left
        
        return (node.key, node.value)
    
    def maximum(self) -> Optional[Tuple[Any, Any]]:
        if not self.root:
            return None
        
        node = self.root
        while node.right:
            node = node.right
        
        return (node.key, node.value)
    
    def clear(self):
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
        return {
            "root": self.root.to_dict() if self.root else None,
            "size": self._size
        }
    
    def to_list(self) -> List[Tuple[Any, Any]]:
        return list(self.inorder())
    
    @classmethod
    def from_list(cls, items: List[Tuple[Any, Any]]) -> "AVLTree":
        tree = cls()
        for key, value in items:
            tree.insert(key, value)
        return tree


