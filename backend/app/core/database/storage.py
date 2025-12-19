"""
Custom Storage Layer

Redis-based storage with custom DSA structures for in-memory operations.
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
from app.core.database.redis_client import get_redis_client, RedisClient


class Storage:
    """
    Redis-based storage with custom DSA structures for in-memory operations.
    
    Features:
    - Persistent storage in Redis
    - In-memory caching with DSA
    - Thread-safe operations
    - Automatic indexing
    """
    
    # Redis key prefixes
    KEY_ENTITY = "entity:{}"
    KEY_GRAPH = "graph:entity_graph"
    KEY_INDEX_TIMESTAMP = "index:timestamp"
    KEY_INDEX_TYPE = "index:type:{}"
    KEY_INDEX_VALUE = "index:value"
    
    def __init__(self, data_dir: Path = None, redis_client: Optional[RedisClient] = None):
        """Initialize storage.
        
        Args:
            data_dir: Base directory for data storage (for fallback/migration)
            redis_client: Optional Redis client instance
        """
        self.data_dir = data_dir or settings.DATA_DIR
        self._ensure_directories()
        
        # Redis client
        try:
            self.redis = redis_client or get_redis_client()
            self._use_redis = self.redis.is_connected()
        except Exception as e:
            logger.warning(f"Redis not available, falling back to file storage: {e}")
            self.redis = None
            self._use_redis = False
        
        # In-memory structures (for fast operations)
        self._entity_graph = Graph(directed=True)
        self._entity_index = AVLTree()  # Index by timestamp
        self._type_index = HashMap()    # Index by entity type
        self._value_trie = Trie()       # Prefix search on values
        self._seen_filter = BloomFilter(expected_items=1000000)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Load existing data
        self._load_data()
    
    def _ensure_directories(self):
        """Create necessary directories."""
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
        """Load existing data from Redis or files (fallback)."""
        if self._use_redis:
            # Load from Redis
            try:
                # Load graph
                graph_data = self.redis.get_json(self.KEY_GRAPH)
                if graph_data:
                    self._entity_graph = Graph.from_dict(graph_data)
                
                # Load entities and rebuild indices
                entity_keys = self.redis.keys(self.KEY_ENTITY.format("*"))
                for key in entity_keys:
                    try:
                        entity_id = key.replace("entity:", "")
                        entity = self.redis.get_json(key)
                        if entity:
                            self._index_entity(entity)
                    except Exception as e:
                        logger.warning(f"Failed to load entity {key}: {e}")
                        continue
            except Exception as e:
                logger.error(f"Failed to load data from Redis: {e}")
                # Fallback to file loading
                self._load_data_from_files()
        else:
            # Fallback to file loading
            self._load_data_from_files()
    
    def _load_data_from_files(self):
        """Load existing data from files (fallback)."""
        # Load graph
        graph_file = self.data_dir / "graph" / "entity_graph.json"
        if graph_file.exists():
            try:
                with open(graph_file, 'r') as f:
                    data = json.load(f)
                    self._entity_graph = Graph.from_dict(data)
            except Exception:
                pass
        
        # Load entities and rebuild indices
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
        """Save graph to Redis or file (fallback)."""
        graph_data = self._entity_graph.to_dict()
        
        if self._use_redis:
            try:
                self.redis.set_json(self.KEY_GRAPH, graph_data)
            except Exception as e:
                logger.error(f"Failed to save graph to Redis: {e}")
                # Fallback to file
                self._save_graph_to_file(graph_data)
        else:
            self._save_graph_to_file(graph_data)
    
    def _save_graph_to_file(self, graph_data: dict):
        """Save graph to file (fallback)."""
        graph_file = self.data_dir / "graph" / "entity_graph.json"
        with open(graph_file, 'w') as f:
            json.dump(graph_data, f, default=str)
    
    def _index_entity(self, entity: dict):
        """Add entity to in-memory and Redis indices."""
        entity_id = entity.get("id")
        entity_type = entity.get("type")
        value = entity.get("value", "")
        timestamp = entity.get("created_at", datetime.utcnow().isoformat())
        
        # Parse timestamp for Redis sorted set (use timestamp as score)
        try:
            timestamp_score = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
        except:
            timestamp_score = datetime.utcnow().timestamp()
        
        # Add to type index (in-memory and Redis)
        if entity_type:
            # In-memory
            entities = self._type_index.get(entity_type, [])
            if entity_id not in entities:
                entities.append(entity_id)
            self._type_index.put(entity_type, entities)
        
            # Redis
            if self._use_redis:
                try:
                    self.redis.sadd(self.KEY_INDEX_TYPE.format(entity_type), entity_id)
                except Exception as e:
                    logger.warning(f"Failed to add to Redis type index: {e}")
        
        # Add to trie for prefix search (in-memory only - Redis doesn't have trie)
        if value:
            self._value_trie.insert(value.lower(), entity_id)
        
        # Add to bloom filter (in-memory only)
        self._seen_filter.add(entity_id)
        if value:
            self._seen_filter.add(value)
        
        # Add to AVL tree by timestamp (in-memory)
        self._entity_index.insert(timestamp, entity_id)
        
        # Add to Redis timestamp index (sorted set)
        if self._use_redis:
            try:
                self.redis.zadd(self.KEY_INDEX_TIMESTAMP, {entity_id: timestamp_score})
            except Exception as e:
                logger.warning(f"Failed to add to Redis timestamp index: {e}")
        
        # Add to graph
        self._entity_graph.add_node(
            entity_id,
            label=value,
            node_type=entity_type,
            data=entity
        )
    
    # ==================== Entity Operations ====================
    
    def save_entity(self, entity: dict) -> str:
        """Save an entity to storage.
        
        Args:
            entity: Entity dictionary with at least 'id' field
            
        Returns:
            Entity ID
        """
        with self._lock:
            entity_id = entity.get("id")
            if not entity_id:
                raise ValueError("Entity must have an 'id' field")
            
            # Save to Redis or file (fallback)
            if self._use_redis:
                try:
                    self.redis.set_json(self.KEY_ENTITY.format(entity_id), entity)
                except Exception as e:
                    logger.error(f"Failed to save entity to Redis: {e}")
                    # Fallback to file
                    self._save_entity_to_file(entity_id, entity)
            else:
                self._save_entity_to_file(entity_id, entity)
            
            # Update indices
            self._index_entity(entity)
            
            return entity_id
    
    def _save_entity_to_file(self, entity_id: str, entity: dict):
        """Save entity to file (fallback)."""
        entity_file = self.data_dir / "entities" / f"{entity_id}.json"
        with open(entity_file, 'w') as f:
            json.dump(entity, f, default=str, indent=2)
    
    def get_entity(self, entity_id: str) -> Optional[dict]:
        """Get an entity by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Entity dictionary or None
        """
        # Quick check with bloom filter (may have false positives)
        if not self._seen_filter.contains(entity_id):
            return None
        
        # Get from Redis or file (fallback)
        if self._use_redis:
            try:
                entity = self.redis.get_json(self.KEY_ENTITY.format(entity_id))
                if entity:
                    return entity
            except Exception as e:
                logger.warning(f"Failed to get entity from Redis: {e}")
        
        # Fallback to file
        entity_file = self.data_dir / "entities" / f"{entity_id}.json"
        if entity_file.exists():
            try:
                with open(entity_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return None
    
    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            True if deleted
        """
        with self._lock:
            deleted = False
            
            # Delete from Redis
            if self._use_redis:
                try:
                    # Get entity first to know its type for index cleanup
                    entity = self.redis.get_json(self.KEY_ENTITY.format(entity_id))
                    if entity:
                        entity_type = entity.get("type")
                        
                        # Delete from Redis
                        self.redis.delete(self.KEY_ENTITY.format(entity_id))
                        
                        # Remove from indices
                        if entity_type:
                            self.redis.srem(self.KEY_INDEX_TYPE.format(entity_type), entity_id)
                        self.redis.zrem(self.KEY_INDEX_TIMESTAMP, entity_id)
                        
                        deleted = True
                except Exception as e:
                    logger.warning(f"Failed to delete entity from Redis: {e}")
            
            # Delete from file (fallback or cleanup)
            entity_file = self.data_dir / "entities" / f"{entity_id}.json"
            if entity_file.exists():
                try:
                    os.remove(entity_file)
                    deleted = True
                except Exception:
                    pass
            
            # Remove from in-memory structures
            # Note: Can't remove from bloom filter (it's probabilistic)
            self._entity_graph.remove_node(entity_id)
            
            return deleted
    
    def search_by_prefix(self, prefix: str, limit: int = 100) -> List[str]:
        """Search entities by value prefix.
        
        Args:
            prefix: Prefix to search for
            limit: Maximum results
            
        Returns:
            List of entity IDs
        """
        matches = self._value_trie.get_prefix_matches(prefix.lower(), limit)
        return [entity_id for _, entity_id in matches]
    
    def get_by_type(self, entity_type: str) -> List[str]:
        """Get all entity IDs of a specific type.
        
        Args:
            entity_type: Type to filter by
            
        Returns:
            List of entity IDs
        """
        if self._use_redis:
            try:
                # Get from Redis set
                return list(self.redis.smembers(self.KEY_INDEX_TYPE.format(entity_type)))
            except Exception as e:
                logger.warning(f"Failed to get entities by type from Redis: {e}")
                # Fallback to in-memory
                return self._type_index.get(entity_type, [])
        else:
            return self._type_index.get(entity_type, [])
    
    def exists(self, value: str) -> bool:
        """Quick check if a value exists (may have false positives).
        
        Args:
            value: Value to check
            
        Returns:
            True if probably exists, False if definitely not
        """
        return self._seen_filter.contains(value)
    
    # ==================== Graph Operations ====================
    
    def add_relationship(self, source_id: str, target_id: str, 
                        relation: str, weight: float = 1.0, metadata: dict = None):
        """Add a relationship between entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relation: Relationship type
            weight: Edge weight
            metadata: Additional edge data
        """
        with self._lock:
            self._entity_graph.add_edge(
                source_id, target_id,
                weight=weight,
                relation=relation,
                metadata=metadata or {}
            )
            self._save_graph()
    
    def get_neighbors(self, entity_id: str, depth: int = 1) -> List[str]:
        """Get neighboring entity IDs.
        
        Args:
            entity_id: Starting entity
            depth: Maximum depth
            
        Returns:
            List of neighbor entity IDs
        """
        return list(self._entity_graph.get_neighbors(entity_id, depth))
    
    def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find path between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            
        Returns:
            List of entity IDs in path, or None
        """
        return self._entity_graph.shortest_path_bfs(source_id, target_id)
    
    def get_graph_data(self) -> dict:
        """Get full graph data for visualization.
        
        Returns:
            Dictionary with nodes and edges
        """
        return self._entity_graph.to_dict()
    
    # ==================== Statistics ====================
    
    def stats(self) -> dict:
        """Get storage statistics."""
        entity_count = 0
        if self._use_redis:
            try:
                entity_keys = self.redis.keys(self.KEY_ENTITY.format("*"))
                entity_count = len(entity_keys)
            except Exception:
                # Fallback to file count
                entity_count = len(list((self.data_dir / "entities").glob("*.json")))
        else:
            entity_count = len(list((self.data_dir / "entities").glob("*.json")))
        
        return {
            "entities": entity_count,
            "graph_nodes": self._entity_graph.node_count,
            "graph_edges": self._entity_graph.edge_count,
            "index_size": len(self._entity_index),
            "bloom_filter": self._seen_filter.stats(),
            "storage_backend": "redis" if self._use_redis else "file"
        }


