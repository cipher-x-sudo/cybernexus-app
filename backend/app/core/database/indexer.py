"""
Custom Indexer

Indexing layer using AVL Trees and Tries for fast lookups.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.core.dsa import AVLTree, Trie, HashMap


class Indexer:
    """
    Multi-index manager using custom DSA.
    
    Supports:
    - Primary key index (AVL Tree)
    - Text prefix index (Trie)
    - Secondary indices (HashMap)
    - Range queries
    """
    
    def __init__(self):
        """Initialize indexer."""
        self._primary_index = AVLTree()
        self._text_index = Trie()
        self._secondary_indices: Dict[str, AVLTree] = {}
        self._reverse_index = HashMap()  # Value -> keys mapping
    
    def create_index(self, name: str):
        """Create a new secondary index.
        
        Args:
            name: Index name
        """
        if name not in self._secondary_indices:
            self._secondary_indices[name] = AVLTree()
    
    def drop_index(self, name: str) -> bool:
        """Drop a secondary index.
        
        Args:
            name: Index name
            
        Returns:
            True if dropped
        """
        if name in self._secondary_indices:
            del self._secondary_indices[name]
            return True
        return False
    
    def index(self, key: Any, value: Any, secondary_keys: Dict[str, Any] = None):
        """Index a key-value pair.
        
        Args:
            key: Primary key
            value: Value to store
            secondary_keys: Optional secondary index keys
        """
        # Primary index
        self._primary_index.insert(key, value)
        
        # Text index if value is string
        if isinstance(value, str):
            self._text_index.insert(value.lower(), key)
        elif isinstance(value, dict):
            # Index searchable text fields
            for field in ['value', 'title', 'description', 'label']:
                if field in value and isinstance(value[field], str):
                    self._text_index.insert(value[field].lower(), key)
        
        # Secondary indices
        if secondary_keys:
            for index_name, index_value in secondary_keys.items():
                if index_name in self._secondary_indices:
                    self._secondary_indices[index_name].insert(index_value, key)
                    
                    # Reverse index
                    existing = self._reverse_index.get(f"{index_name}:{index_value}", [])
                    if key not in existing:
                        existing.append(key)
                    self._reverse_index.put(f"{index_name}:{index_value}", existing)
    
    def remove(self, key: Any):
        """Remove a key from all indices.
        
        Args:
            key: Primary key to remove
        """
        self._primary_index.delete(key)
        # Note: Trie doesn't support efficient removal by value
        # Secondary indices would need reverse mapping
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value by primary key.
        
        Args:
            key: Primary key
            
        Returns:
            Value or None
        """
        return self._primary_index.search(key)
    
    def search_text(self, prefix: str, limit: int = 100) -> List[Any]:
        """Search by text prefix.
        
        Args:
            prefix: Text prefix
            limit: Maximum results
            
        Returns:
            List of matching keys
        """
        matches = self._text_index.get_prefix_matches(prefix.lower(), limit)
        return [key for _, key in matches]
    
    def range_query(self, index_name: str, low: Any, high: Any) -> List[Tuple[Any, Any]]:
        """Range query on an index.
        
        Args:
            index_name: Index to query ('primary' or secondary index name)
            low: Lower bound
            high: Upper bound
            
        Returns:
            List of (key, value) tuples
        """
        if index_name == 'primary':
            return self._primary_index.range_query(low, high)
        elif index_name in self._secondary_indices:
            return self._secondary_indices[index_name].range_query(low, high)
        return []
    
    def get_by_secondary(self, index_name: str, value: Any) -> List[Any]:
        """Get primary keys by secondary index value.
        
        Args:
            index_name: Secondary index name
            value: Value to search for
            
        Returns:
            List of primary keys
        """
        return self._reverse_index.get(f"{index_name}:{value}", [])
    
    def count(self) -> int:
        """Get total indexed items."""
        return len(self._primary_index)
    
    def stats(self) -> dict:
        """Get indexer statistics."""
        return {
            "primary_index_size": len(self._primary_index),
            "primary_index_height": self._primary_index.height(),
            "text_index_size": len(self._text_index),
            "secondary_indices": {
                name: len(idx) for name, idx in self._secondary_indices.items()
            }
        }


class TimeSeriesIndexer:
    """
    Specialized indexer for time-series data.
    Uses AVL Tree for efficient range queries by timestamp.
    """
    
    def __init__(self):
        """Initialize time-series indexer."""
        self._time_index = AVLTree()
        self._id_map = HashMap()  # ID -> timestamp mapping
    
    def add(self, item_id: str, timestamp: datetime, data: Any):
        """Add a time-series entry.
        
        Args:
            item_id: Unique identifier
            timestamp: Entry timestamp
            data: Entry data
        """
        ts_key = timestamp.timestamp()  # Convert to float for comparison
        
        # Store in time index
        self._time_index.insert(ts_key, {"id": item_id, "timestamp": timestamp, "data": data})
        
        # Store ID mapping
        self._id_map.put(item_id, ts_key)
    
    def get(self, item_id: str) -> Optional[dict]:
        """Get entry by ID.
        
        Args:
            item_id: Entry identifier
            
        Returns:
            Entry data or None
        """
        ts_key = self._id_map.get(item_id)
        if ts_key:
            return self._time_index.search(ts_key)
        return None
    
    def range(self, start: datetime, end: datetime) -> List[dict]:
        """Get entries in time range.
        
        Args:
            start: Start time
            end: End time
            
        Returns:
            List of entries in range
        """
        results = self._time_index.range_query(start.timestamp(), end.timestamp())
        return [value for _, value in results]
    
    def latest(self, n: int = 10) -> List[dict]:
        """Get latest N entries.
        
        Args:
            n: Number of entries
            
        Returns:
            List of latest entries
        """
        # Get all and sort (could be optimized with max-heap)
        all_items = list(self._time_index.inorder())
        all_items.sort(key=lambda x: x[0], reverse=True)
        return [value for _, value in all_items[:n]]
    
    def count(self) -> int:
        """Get total entries."""
        return len(self._time_index)


