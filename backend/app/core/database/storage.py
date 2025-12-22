"""Entity storage and indexing system.

This module provides file-based storage for entities with graph-based relationship
mapping and efficient indexing using custom DSA structures.

This module uses the following DSA concepts from app.core.dsa:
- Graph: Entity relationship mapping and graph operations (BFS, shortest path)
- AVLTree: Timestamp-based entity indexing for O(log n) lookups and range queries
- HashMap: Type-based entity grouping and O(1) lookups
- Trie: Prefix-based entity value searching for autocomplete functionality
- BloomFilter: Efficient entity existence checking and deduplication
"""

import os
import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger

from app.config import settings
from app.core.dsa import Graph, AVLTree, HashMap, Trie, BloomFilter


class Storage:
    
    KEY_ENTITY = "entity:{}"
    KEY_GRAPH = "graph:entity_graph"
    KEY_INDEX_TIMESTAMP = "index:timestamp"
    KEY_INDEX_TYPE = "index:type:{}"
    KEY_INDEX_VALUE = "index:value"
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self._ensure_directories()
        
        self._entity_graph = Graph(directed=True)
        self._entity_index = AVLTree()
        self._type_index = HashMap()
        self._value_trie = Trie()
        self._seen_filter = BloomFilter(expected_items=1000000)
        
        self._lock = threading.RLock()
        
        self._load_data()
    
    def _ensure_directories(self):
        dirs = [
            self.data_dir,
            self.data_dir / "entities",
            self.data_dir / "graph",
            self.data_dir / "indices",
            self.data_dir / "events",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def _load_data(self):
        self._load_data_from_files()
    
    def _load_data_from_files(self):
        graph_file = self.data_dir / "graph" / "entity_graph.json"
        if graph_file.exists():
            try:
                with open(graph_file, 'r') as f:
                    data = json.load(f)
                    self._entity_graph = Graph.from_dict(data)
            except Exception:
                pass
        
        entities_dir = self.data_dir / "entities"
        if entities_dir.exists():
            for entity_file in entities_dir.glob("*.json"):
                try:
                    with open(entity_file, 'r') as f:
                        entity = json.load(f)
                        self._index_entity(entity)
                except Exception:
                    pass
    
    def _save_graph(self):
        graph_data = self._entity_graph.to_dict()
        self._save_graph_to_file(graph_data)
    
    def _save_graph_to_file(self, graph_data: dict):
        graph_file = self.data_dir / "graph" / "entity_graph.json"
        with open(graph_file, 'w') as f:
            json.dump(graph_data, f, default=str)
    
    def _index_entity(self, entity: dict):
        entity_id = entity.get("id")
        entity_type = entity.get("type")
        value = entity.get("value", "")
        timestamp = entity.get("created_at", datetime.utcnow().isoformat())
        
        if entity_type:
            entities = self._type_index.get(entity_type, [])
            if entity_id not in entities:
                entities.append(entity_id)
            self._type_index.put(entity_type, entities)
        
        if value:
            self._value_trie.insert(value.lower(), entity_id)
        
        self._seen_filter.add(entity_id)
        if value:
            self._seen_filter.add(value)
        
        self._entity_index.insert(timestamp, entity_id)
        
        self._entity_graph.add_node(
            entity_id,
            label=value,
            node_type=entity_type,
            data=entity
        )
    
    def save_entity(self, entity: dict) -> str:
        with self._lock:
            entity_id = entity.get("id")
            if not entity_id:
                raise ValueError("Entity must have an 'id' field")
            
            self._save_entity_to_file(entity_id, entity)
            
            self._index_entity(entity)
            
            return entity_id
    
    def _save_entity_to_file(self, entity_id: str, entity: dict):
        entity_file = self.data_dir / "entities" / f"{entity_id}.json"
        with open(entity_file, 'w') as f:
            json.dump(entity, f, default=str, indent=2)
    
    def get_entity(self, entity_id: str) -> Optional[dict]:
        if not self._seen_filter.contains(entity_id):
            return None
        
        entity_file = self.data_dir / "entities" / f"{entity_id}.json"
        if entity_file.exists():
            try:
                with open(entity_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return None
    
    def delete_entity(self, entity_id: str) -> bool:
        with self._lock:
            deleted = False
            
            entity_file = self.data_dir / "entities" / f"{entity_id}.json"
            if entity_file.exists():
                try:
                    os.remove(entity_file)
                    deleted = True
                except Exception:
                    pass
            
            self._entity_graph.remove_node(entity_id)
            
            return deleted
    
    def search_by_prefix(self, prefix: str, limit: int = 100) -> List[str]:
        matches = self._value_trie.get_prefix_matches(prefix.lower(), limit)
        return [entity_id for _, entity_id in matches]
    
    def get_by_type(self, entity_type: str) -> List[str]:
        return self._type_index.get(entity_type, [])
    
    def exists(self, value: str) -> bool:
        return self._seen_filter.contains(value)
    
    def add_relationship(self, source_id: str, target_id: str, 
                        relation: str, weight: float = 1.0, metadata: dict = None):
        with self._lock:
            self._entity_graph.add_edge(
                source_id, target_id,
                weight=weight,
                relation=relation,
                metadata=metadata or {}
            )
            self._save_graph()
    
    def get_neighbors(self, entity_id: str, depth: int = 1) -> List[str]:
        return list(self._entity_graph.get_neighbors(entity_id, depth))
    
    def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        return self._entity_graph.shortest_path_bfs(source_id, target_id)
    
    def get_graph_data(self) -> dict:
        return self._entity_graph.to_dict()
    
    def stats(self) -> dict:
        entity_count = len(list((self.data_dir / "entities").glob("*.json")))
        
        return {
            "entities": entity_count,
            "graph_nodes": self._entity_graph.node_count,
            "graph_edges": self._entity_graph.edge_count,
            "index_size": len(self._entity_index),
            "bloom_filter": self._seen_filter.stats(),
            "storage_backend": "file"
        }


