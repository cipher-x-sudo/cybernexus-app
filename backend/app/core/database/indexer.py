"""Database indexing system.

This module provides indexing capabilities for fast lookups using multiple
index types and text search functionality.

This module uses the following DSA concepts from app.core.dsa:
- AVLTree: Primary and secondary indices for O(log n) key-based lookups and range queries
- Trie: Text index for prefix-based searching and autocomplete
- HashMap: Reverse index mapping for O(1) secondary key lookups
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.core.dsa import AVLTree, Trie, HashMap


class Indexer:
    def __init__(self):
        self._primary_index = AVLTree()
        self._text_index = Trie()
        self._secondary_indices: Dict[str, AVLTree] = {}
        self._reverse_index = HashMap()
    
    def create_index(self, name: str):
        if name not in self._secondary_indices:
            self._secondary_indices[name] = AVLTree()
    
    def drop_index(self, name: str) -> bool:
        if name in self._secondary_indices:
            del self._secondary_indices[name]
            return True
        return False
    
    def index(self, key: Any, value: Any, secondary_keys: Dict[str, Any] = None):
        """Index a key-value pair in all relevant indices.
        
        DSA-USED:
        - AVLTree: Primary and secondary index insertion
        - Trie: Text index insertion for prefix matching
        - HashMap: Reverse index update for secondary key lookups
        
        Args:
            key: Primary key to index
            value: Value to associate with key
            secondary_keys: Optional dictionary of secondary index values
        """
        self._primary_index.insert(key, value)  # DSA-USED: AVLTree
        
        if isinstance(value, str):
            self._text_index.insert(value.lower(), key)  # DSA-USED: Trie
        elif isinstance(value, dict):
            for field in ['value', 'title', 'description', 'label']:
                if field in value and isinstance(value[field], str):
                    self._text_index.insert(value[field].lower(), key)  # DSA-USED: Trie
        
        if secondary_keys:
            for index_name, index_value in secondary_keys.items():
                if index_name in self._secondary_indices:
                    self._secondary_indices[index_name].insert(index_value, key)  # DSA-USED: AVLTree
                    
                    existing = self._reverse_index.get(f"{index_name}:{index_value}", [])  # DSA-USED: HashMap
                    if key not in existing:
                        existing.append(key)
                    self._reverse_index.put(f"{index_name}:{index_value}", existing)  # DSA-USED: HashMap
    
    def remove(self, key: Any):
        """Remove a key from the primary index.
        
        DSA-USED:
        - AVLTree: Key deletion from primary index
        
        Args:
            key: Key to remove
        """
        self._primary_index.delete(key)  # DSA-USED: AVLTree
    
    def get(self, key: Any) -> Optional[Any]:
        """Retrieve value by primary key.
        
        DSA-USED:
        - AVLTree: O(log n) key lookup
        
        Args:
            key: Primary key to look up
        
        Returns:
            Associated value if found, None otherwise
        """
        return self._primary_index.search(key)  # DSA-USED: AVLTree
    
    def search_text(self, prefix: str, limit: int = 100) -> List[Any]:
        """Search for keys by text prefix.
        
        DSA-USED:
        - Trie: Prefix matching for autocomplete functionality
        
        Args:
            prefix: Prefix string to search for
            limit: Maximum number of results
        
        Returns:
            List of keys matching the prefix
        """
        matches = self._text_index.get_prefix_matches(prefix.lower(), limit)  # DSA-USED: Trie
        return [key for _, key in matches]
    
    def range_query(self, index_name: str, low: Any, high: Any) -> List[Tuple[Any, Any]]:
        """Query keys within a range.
        
        DSA-USED:
        - AVLTree: Range query for O(log n + k) complexity
        
        Args:
            index_name: Index name ('primary' or secondary index name)
            low: Lower bound (inclusive)
            high: Upper bound (inclusive)
        
        Returns:
            List of (key, value) tuples in the specified range
        """
        if index_name == 'primary':
            return self._primary_index.range_query(low, high)  # DSA-USED: AVLTree
        elif index_name in self._secondary_indices:
            return self._secondary_indices[index_name].range_query(low, high)  # DSA-USED: AVLTree
        return []
    
    def get_by_secondary(self, index_name: str, value: Any) -> List[Any]:
        """Get keys by secondary index value.
        
        DSA-USED:
        - HashMap: O(1) reverse index lookup
        
        Args:
            index_name: Secondary index name
            value: Value to look up
        
        Returns:
            List of primary keys associated with the value
        """
        return self._reverse_index.get(f"{index_name}:{value}", [])  # DSA-USED: HashMap
    
    def count(self) -> int:
        return len(self._primary_index)
    
    def stats(self) -> dict:
        return {
            "primary_index_size": len(self._primary_index),
            "primary_index_height": self._primary_index.height(),
            "text_index_size": len(self._text_index),
            "secondary_indices": {
                name: len(idx) for name, idx in self._secondary_indices.items()
            }
        }


class TimeSeriesIndexer:
    def __init__(self):
        self._time_index = AVLTree()
        self._id_map = HashMap()
    
    def add(self, item_id: str, timestamp: datetime, data: Any):
        """Add an item to the time series index.
        
        DSA-USED:
        - AVLTree: Timestamp-based insertion for chronological ordering
        - HashMap: ID to timestamp mapping for O(1) lookups
        
        Args:
            item_id: Unique item identifier
            timestamp: Timestamp for the item
            data: Item data to store
        """
        ts_key = timestamp.timestamp()
        
        self._time_index.insert(ts_key, {"id": item_id, "timestamp": timestamp, "data": data})  # DSA-USED: AVLTree
        
        self._id_map.put(item_id, ts_key)  # DSA-USED: HashMap
    
    def get(self, item_id: str) -> Optional[dict]:
        """Get item by ID using time index.
        
        DSA-USED:
        - HashMap: ID to timestamp lookup
        - AVLTree: Timestamp-based item retrieval
        
        Args:
            item_id: Item identifier
        
        Returns:
            Item dictionary if found, None otherwise
        """
        ts_key = self._id_map.get(item_id)  # DSA-USED: HashMap
        if ts_key:
            return self._time_index.search(ts_key)  # DSA-USED: AVLTree
        return None
    
    def range(self, start: datetime, end: datetime) -> List[dict]:
        """Get items within a time range.
        
        DSA-USED:
        - AVLTree: Range query for time-based filtering
        
        Args:
            start: Start timestamp (inclusive)
            end: End timestamp (inclusive)
        
        Returns:
            List of item dictionaries in the time range
        """
        results = self._time_index.range_query(start.timestamp(), end.timestamp())  # DSA-USED: AVLTree
        return [value for _, value in results]
    
    def latest(self, n: int = 10) -> List[dict]:
        all_items = list(self._time_index.inorder())
        all_items.sort(key=lambda x: x[0], reverse=True)
        return [value for _, value in all_items[:n]]
    
    def count(self) -> int:
        return len(self._time_index)


