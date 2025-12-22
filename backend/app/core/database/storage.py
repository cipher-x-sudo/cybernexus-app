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
        """Create required data directories if they don't exist."""
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
        """Load persisted data into memory structures."""
        self._load_data_from_files()
    
    def _load_data_from_files(self):
        """Load graph data from persisted files.
        
        DSA-USED:
        - Graph: Deserialization from JSON representation
        """
        graph_file = self.data_dir / "graph" / "entity_graph.json"
        if graph_file.exists():
            try:
                with open(graph_file, 'r') as f:
                    data = json.load(f)
                    self._entity_graph = Graph.from_dict(data)  # DSA-USED: Graph
            except Exception:
                pass
        
        # Load entities from JSON files and rebuild indices
        entities_dir = self.data_dir / "entities"
        if entities_dir.exists():
            for entity_file in entities_dir.glob("*.json"):
                try:
                    with open(entity_file, 'r') as f:
                        entity = json.load(f)
                        self._index_entity(entity)  # Rebuild all indices
                except Exception:
                    pass
    
    def _save_graph(self):
        """Save graph to file.
        
        DSA-USED:
        - Graph: Serialization to dictionary representation
        """
        graph_data = self._entity_graph.to_dict()  # DSA-USED: Graph
        self._save_graph_to_file(graph_data)
    
    def _save_graph_to_file(self, graph_data: dict):
        graph_file = self.data_dir / "graph" / "entity_graph.json"
        with open(graph_file, 'w') as f:
            json.dump(graph_data, f, default=str)
    
    def _index_entity(self, entity: dict):
        """Index an entity in all DSA structures.
        
        DSA-USED:
        - HashMap: Type-based entity grouping
        - Trie: Value-based prefix indexing
        - BloomFilter: Entity existence checking
        - AVLTree: Timestamp-based indexing
        - Graph: Entity node creation
        
        Args:
            entity: Entity dictionary to index
        """
        entity_id = entity.get("id")
        entity_type = entity.get("type")
        value = entity.get("value", "")
        timestamp = entity.get("created_at", datetime.utcnow().isoformat())
        
        if entity_type:
            entities = self._type_index.get(entity_type, [])  # DSA-USED: HashMap
            if entity_id not in entities:
                entities.append(entity_id)
            self._type_index.put(entity_type, entities)  # DSA-USED: HashMap
        
        if value:
            self._value_trie.insert(value.lower(), entity_id)  # DSA-USED: Trie
        
        self._seen_filter.add(entity_id)  # DSA-USED: BloomFilter
        if value:
            self._seen_filter.add(value)  # DSA-USED: BloomFilter
        
        self._entity_index.insert(timestamp, entity_id)  # DSA-USED: AVLTree
        
        self._entity_graph.add_node(
            entity_id,
            label=value,
            node_type=entity_type,
            data=entity
        )  # DSA-USED: Graph
    
    def save_entity(self, entity: dict) -> str:
        """Save entity to file and update all indices (thread-safe)."""
        with self._lock:
            entity_id = entity.get("id")
            if not entity_id:
                raise ValueError("Entity must have an 'id' field")
            
            self._save_entity_to_file(entity_id, entity)
            
            # Update all indexing structures
            self._index_entity(entity)
            
            return entity_id
    
    def _save_entity_to_file(self, entity_id: str, entity: dict):
        """Persist entity to JSON file."""
        entity_file = self.data_dir / "entities" / f"{entity_id}.json"
        with open(entity_file, 'w') as f:
            json.dump(entity, f, default=str, indent=2)
    
    def get_entity(self, entity_id: str) -> Optional[dict]:
        """Retrieve an entity by ID.
        
        DSA-USED:
        - BloomFilter: Fast existence check before file access
        
        Args:
            entity_id: Entity identifier
        
        Returns:
            Entity dictionary if found, None otherwise
        """
        if not self._seen_filter.contains(entity_id):  # DSA-USED: BloomFilter
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
        """Delete an entity and remove from graph.
        
        DSA-USED:
        - Graph: Node removal from adjacency list
        
        Args:
            entity_id: Entity identifier to delete
        
        Returns:
            True if entity was deleted, False otherwise
        """
        with self._lock:
            deleted = False
            
            # Remove entity file
            entity_file = self.data_dir / "entities" / f"{entity_id}.json"
            if entity_file.exists():
                try:
                    os.remove(entity_file)
                    deleted = True
                except Exception:
                    pass
            
            # Remove from graph structure
            self._entity_graph.remove_node(entity_id)  # DSA-USED: Graph
            
            return deleted
    
    def search_by_prefix(self, prefix: str, limit: int = 100) -> List[str]:
        """Search entities by value prefix.
        
        DSA-USED:
        - Trie: Prefix matching for autocomplete functionality
        
        Args:
            prefix: Prefix string to search for
            limit: Maximum number of results
        
        Returns:
            List of entity IDs matching the prefix
        """
        matches = self._value_trie.get_prefix_matches(prefix.lower(), limit)  # DSA-USED: Trie
        return [entity_id for _, entity_id in matches]
    
    def get_by_type(self, entity_type: str) -> List[str]:
        """Get all entity IDs of a specific type.
        
        DSA-USED:
        - HashMap: O(1) lookup by entity type
        
        Args:
            entity_type: Type to filter by
        
        Returns:
            List of entity IDs of the specified type
        """
        return self._type_index.get(entity_type, [])  # DSA-USED: HashMap
    
    def exists(self, value: str) -> bool:
        """Check if a value exists using bloom filter.
        
        DSA-USED:
        - BloomFilter: Probabilistic membership test
        
        Args:
            value: Value to check
        
        Returns:
            True if value possibly exists, False if definitely doesn't
        """
        return self._seen_filter.contains(value)  # DSA-USED: BloomFilter
    
    def add_relationship(self, source_id: str, target_id: str, 
                        relation: str, weight: float = 1.0, metadata: dict = None):
        """Add a relationship edge between two entities.
        
        DSA-USED:
        - Graph: Edge creation in adjacency list
        
        Args:
            source_id: Source entity identifier
            target_id: Target entity identifier
            relation: Relationship type
            weight: Edge weight
            metadata: Optional edge metadata
        """
        with self._lock:
            self._entity_graph.add_edge(
                source_id, target_id,
                weight=weight,
                relation=relation,
                metadata=metadata or {}
            )  # DSA-USED: Graph
            self._save_graph()
    
    def get_neighbors(self, entity_id: str, depth: int = 1) -> List[str]:
        """Get neighboring entities up to specified depth.
        
        DSA-USED:
        - Graph: Neighbor retrieval using BFS traversal
        
        Args:
            entity_id: Entity identifier
            depth: Maximum depth to traverse
        
        Returns:
            List of neighboring entity IDs
        """
        return list(self._entity_graph.get_neighbors(entity_id, depth))  # DSA-USED: Graph
    
    def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find shortest path between two entities.
        
        DSA-USED:
        - Graph: BFS shortest path algorithm
        
        Args:
            source_id: Starting entity identifier
            target_id: Target entity identifier
        
        Returns:
            List of entity IDs representing the path, or None if no path exists
        """
        return self._entity_graph.shortest_path_bfs(source_id, target_id)  # DSA-USED: Graph
    
    def get_graph_data(self) -> dict:
        """Get serialized graph representation.
        
        DSA-USED:
        - Graph: Serialization to dictionary
        
        Returns:
            Dictionary representation of the entity graph
        """
        return self._entity_graph.to_dict()  # DSA-USED: Graph
    
    def stats(self) -> dict:
        """Get statistics about storage structures.
        
        DSA-USED:
        - Graph: Node and edge count retrieval
        - AVLTree: Size retrieval
        - BloomFilter: Statistics retrieval
        
        Returns:
            Dictionary with storage statistics
        """
        entity_count = len(list((self.data_dir / "entities").glob("*.json")))
        
        return {
            "entities": entity_count,
            "graph_nodes": self._entity_graph.node_count,  # DSA-USED: Graph
            "graph_edges": self._entity_graph.edge_count,  # DSA-USED: Graph
            "index_size": len(self._entity_index),  # DSA-USED: AVLTree
            "bloom_filter": self._seen_filter.stats(),  # DSA-USED: BloomFilter
            "storage_backend": "file"
        }


