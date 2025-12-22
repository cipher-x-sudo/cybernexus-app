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
        self._primary_index.insert(key, value)
        
        if isinstance(value, str):
            self._text_index.insert(value.lower(), key)
        elif isinstance(value, dict):
            for field in ['value', 'title', 'description', 'label']:
                if field in value and isinstance(value[field], str):
                    self._text_index.insert(value[field].lower(), key)
        
        if secondary_keys:
            for index_name, index_value in secondary_keys.items():
                if index_name in self._secondary_indices:
                    self._secondary_indices[index_name].insert(index_value, key)
                    
                    existing = self._reverse_index.get(f"{index_name}:{index_value}", [])
                    if key not in existing:
                        existing.append(key)
                    self._reverse_index.put(f"{index_name}:{index_value}", existing)
    
    def remove(self, key: Any):
        self._primary_index.delete(key)
    
    def get(self, key: Any) -> Optional[Any]:
        return self._primary_index.search(key)
    
    def search_text(self, prefix: str, limit: int = 100) -> List[Any]:
        matches = self._text_index.get_prefix_matches(prefix.lower(), limit)
        return [key for _, key in matches]
    
    def range_query(self, index_name: str, low: Any, high: Any) -> List[Tuple[Any, Any]]:
        if index_name == 'primary':
            return self._primary_index.range_query(low, high)
        elif index_name in self._secondary_indices:
            return self._secondary_indices[index_name].range_query(low, high)
        return []
    
    def get_by_secondary(self, index_name: str, value: Any) -> List[Any]:
        return self._reverse_index.get(f"{index_name}:{value}", [])
    
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
        ts_key = timestamp.timestamp()
        
        self._time_index.insert(ts_key, {"id": item_id, "timestamp": timestamp, "data": data})
        
        self._id_map.put(item_id, ts_key)
    
    def get(self, item_id: str) -> Optional[dict]:
        ts_key = self._id_map.get(item_id)
        if ts_key:
            return self._time_index.search(ts_key)
        return None
    
    def range(self, start: datetime, end: datetime) -> List[dict]:
        results = self._time_index.range_query(start.timestamp(), end.timestamp())
        return [value for _, value in results]
    
    def latest(self, n: int = 10) -> List[dict]:
        all_items = list(self._time_index.inorder())
        all_items.sort(key=lambda x: x[0], reverse=True)
        return [value for _, value in all_items[:n]]
    
    def count(self) -> int:
        return len(self._time_index)


