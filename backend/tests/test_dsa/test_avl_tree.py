"""
Tests for AVL Tree DSA Implementation
"""

import pytest
from app.core.dsa.avl_tree import AVLTree


class TestAVLTree:
    """Test suite for AVL Tree data structure."""
    
    def test_create_empty_tree(self):
        """Test creating an empty tree."""
        tree = AVLTree()
        assert len(tree) == 0
    
    def test_insert_single(self):
        """Test inserting a single element."""
        tree = AVLTree()
        tree.insert(5, "five")
        
        assert len(tree) == 1
        assert tree.search(5) == "five"
    
    def test_insert_multiple(self):
        """Test inserting multiple elements."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        assert len(tree) == 3
        assert tree.search(5) == "five"
        assert tree.search(3) == "three"
        assert tree.search(7) == "seven"
    
    def test_insert_duplicate_updates(self):
        """Test that inserting duplicate key updates value."""
        tree = AVLTree()
        tree.insert(5, "five")
        result = tree.insert(5, "FIVE")
        
        assert not result  # Returns False for update
        assert len(tree) == 1
        assert tree.search(5) == "FIVE"
    
    def test_search_missing(self):
        """Test searching for missing key."""
        tree = AVLTree()
        tree.insert(5, "five")
        
        assert tree.search(10) is None
    
    def test_delete(self):
        """Test deleting elements."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        assert tree.delete(3)
        assert len(tree) == 2
        assert tree.search(3) is None
    
    def test_delete_missing(self):
        """Test deleting non-existent key."""
        tree = AVLTree()
        tree.insert(5, "five")
        
        assert not tree.delete(10)
    
    def test_delete_root(self):
        """Test deleting root node."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        assert tree.delete(5)
        assert tree.search(5) is None
        assert tree.search(3) == "three"
        assert tree.search(7) == "seven"
    
    def test_balance_after_inserts(self):
        """Test that tree remains balanced after inserts."""
        tree = AVLTree()
        
        # Insert in ascending order (would create unbalanced tree without rebalancing)
        for i in range(10):
            tree.insert(i, f"value_{i}")
        
        assert tree.is_balanced()
    
    def test_balance_after_deletes(self):
        """Test that tree remains balanced after deletes."""
        tree = AVLTree()
        
        for i in range(10):
            tree.insert(i, f"value_{i}")
        
        for i in range(5):
            tree.delete(i)
        
        assert tree.is_balanced()
    
    def test_inorder_traversal(self):
        """Test in-order traversal returns sorted order."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        tree.insert(1, "one")
        tree.insert(9, "nine")
        
        keys = [k for k, v in tree.inorder()]
        
        assert keys == [1, 3, 5, 7, 9]
    
    def test_preorder_traversal(self):
        """Test pre-order traversal."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        keys = [k for k, v in tree.preorder()]
        
        assert len(keys) == 3
        assert keys[0] == 5  # Root comes first
    
    def test_postorder_traversal(self):
        """Test post-order traversal."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        keys = [k for k, v in tree.postorder()]
        
        assert len(keys) == 3
        assert keys[-1] == 5  # Root comes last
    
    def test_level_order_traversal(self):
        """Test level-order (BFS) traversal."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        keys = [k for k, v in tree.level_order()]
        
        assert len(keys) == 3
        assert keys[0] == 5  # Root at level 0
    
    def test_range_query(self):
        """Test range query."""
        tree = AVLTree()
        for i in range(1, 11):
            tree.insert(i, f"value_{i}")
        
        result = tree.range_query(3, 7)
        keys = [k for k, v in result]
        
        assert keys == [3, 4, 5, 6, 7]
    
    def test_floor(self):
        """Test floor operation."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(10, "ten")
        tree.insert(15, "fifteen")
        
        assert tree.floor(12) == (10, "ten")
        assert tree.floor(10) == (10, "ten")
        assert tree.floor(3) is None
    
    def test_ceiling(self):
        """Test ceiling operation."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(10, "ten")
        tree.insert(15, "fifteen")
        
        assert tree.ceiling(7) == (10, "ten")
        assert tree.ceiling(10) == (10, "ten")
        assert tree.ceiling(20) is None
    
    def test_minimum(self):
        """Test finding minimum."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        assert tree.minimum() == (3, "three")
    
    def test_maximum(self):
        """Test finding maximum."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        assert tree.maximum() == (7, "seven")
    
    def test_minimum_maximum_empty(self):
        """Test min/max on empty tree."""
        tree = AVLTree()
        
        assert tree.minimum() is None
        assert tree.maximum() is None
    
    def test_contains(self):
        """Test __contains__ operator."""
        tree = AVLTree()
        tree.insert(5, "five")
        
        assert 5 in tree
        assert 10 not in tree
    
    def test_iteration(self):
        """Test iterating over tree."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        pairs = list(tree)
        keys = [k for k, v in pairs]
        
        assert keys == [3, 5, 7]
    
    def test_clear(self):
        """Test clearing the tree."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        
        tree.clear()
        
        assert len(tree) == 0
        assert tree.root is None
    
    def test_height(self):
        """Test getting tree height."""
        tree = AVLTree()
        assert tree.height() == 0
        
        tree.insert(5, "five")
        assert tree.height() == 1
        
        tree.insert(3, "three")
        tree.insert(7, "seven")
        assert tree.height() == 2
    
    def test_from_list(self):
        """Test building tree from list."""
        items = [(5, "five"), (3, "three"), (7, "seven")]
        tree = AVLTree.from_list(items)
        
        assert len(tree) == 3
        assert tree.search(5) == "five"
    
    def test_to_list(self):
        """Test converting tree to list."""
        tree = AVLTree()
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        items = tree.to_list()
        
        assert items == [(3, "three"), (5, "five"), (7, "seven")]
    
    def test_custom_comparator(self):
        """Test using custom comparison function."""
        # Reverse order
        tree = AVLTree(compare=lambda a, b: -1 if a > b else (1 if a < b else 0))
        tree.insert(5, "five")
        tree.insert(3, "three")
        tree.insert(7, "seven")
        
        keys = [k for k, v in tree.inorder()]
        
        assert keys == [7, 5, 3]  # Reversed order


