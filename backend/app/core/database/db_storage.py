"""
Database-Backed Storage Layer

PostgreSQL-based storage with user scoping. Replaces Redis storage.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.orm import selectinload
from loguru import logger
import uuid

from app.core.database.models import (
    Entity, GraphNode, GraphEdge, User
)
from app.core.dsa import Graph


class DBStorage:
    """
    Database-backed storage with user scoping.
    
    All operations are scoped to a user_id, except for admins who can access all data.
    """
    
    def __init__(self, db: AsyncSession, user_id: Optional[str] = None, is_admin: bool = False):
        """
        Initialize database storage.
        
        Args:
            db: Database session
            user_id: User ID for scoping (None for admin access to all)
            is_admin: Whether user is admin (can access all data)
        """
        self.db = db
        self.user_id = user_id
        self.is_admin = is_admin
    
    def _get_user_filter(self):
        """Get user filter for queries (empty for admins)."""
        if self.is_admin:
            return None
        return Entity.user_id == self.user_id
    
    # ==================== Entity Operations ====================
    
    async def save_entity(self, entity: dict, user_id: Optional[str] = None) -> str:
        """
        Save an entity to storage.
        
        Args:
            entity: Entity dictionary with at least 'id' field
            user_id: User ID (overrides instance user_id if provided)
            
        Returns:
            Entity ID
        """
        entity_id = entity.get("id")
        if not entity_id:
            raise ValueError("Entity must have an 'id' field")
        
        # Use provided user_id or instance user_id
        owner_id = user_id or self.user_id
        if not owner_id:
            raise ValueError("user_id must be provided")
        
        # Check if entity exists
        result = await self.db.execute(
            select(Entity).where(Entity.id == entity_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing entity (only if user owns it or is admin)
            if not self.is_admin and existing.user_id != owner_id:
                raise PermissionError("Cannot update entity owned by another user")
            
            existing.type = entity.get("type", existing.type)
            existing.value = entity.get("value", existing.value)
            existing.severity = entity.get("severity", existing.severity)
            existing.meta_data = entity.get("metadata", existing.meta_data) or {}
        else:
            # Create new entity
            db_entity = Entity(
                id=entity_id,
                user_id=owner_id,
                type=entity.get("type", "unknown"),
                value=entity.get("value", ""),
                severity=entity.get("severity", "info"),
                meta_data=entity.get("metadata", {}) or {}
            )
            self.db.add(db_entity)
        
        await self.db.commit()
        return entity_id
    
    async def get_entity(self, entity_id: str) -> Optional[dict]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Entity dictionary or None
        """
        query = select(Entity).where(Entity.id == entity_id)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Entity.user_id == self.user_id)
        
        result = await self.db.execute(query)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return None
        
        return {
            "id": entity.id,
            "type": entity.type,
            "value": entity.value,
            "severity": entity.severity,
            "metadata": entity.meta_data or {},  # Map meta_data back to metadata in API response
            "created_at": entity.created_at.isoformat() if entity.created_at else None
        }
    
    async def delete_entity(self, entity_id: str) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            True if deleted
        """
        query = select(Entity).where(Entity.id == entity_id)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Entity.user_id == self.user_id)
        
        result = await self.db.execute(query)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return False
        
        # Delete related graph nodes and edges
        # Get graph nodes for this entity
        node_result = await self.db.execute(
            select(GraphNode).where(GraphNode.entity_id == entity_id)
        )
        nodes = node_result.scalars().all()
        node_ids = [node.id for node in nodes]
        
        if node_ids:
            # Delete edges connected to these nodes
            await self.db.execute(
                delete(GraphEdge).where(
                    or_(
                        GraphEdge.source_id.in_(node_ids),
                        GraphEdge.target_id.in_(node_ids)
                    )
                )
            )
            # Delete the nodes
            await self.db.execute(
                delete(GraphNode).where(GraphNode.entity_id == entity_id)
            )
        
        # Delete the entity using delete statement
        await self.db.execute(
            delete(Entity).where(Entity.id == entity_id)
        )
        await self.db.commit()
        
        return True
    
    async def search_by_prefix(self, prefix: str, limit: int = 100) -> List[str]:
        """
        Search entities by value prefix.
        
        Args:
            prefix: Prefix to search for
            limit: Maximum results
            
        Returns:
            List of entity IDs
        """
        query = select(Entity.id).where(Entity.value.ilike(f"{prefix}%"))
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Entity.user_id == self.user_id)
        
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        return [row[0] for row in result.fetchall()]
    
    async def get_by_type(self, entity_type: str) -> List[dict]:
        """
        Get all entities of a specific type.
        
        Args:
            entity_type: Type to filter by
            
        Returns:
            List of entity dictionaries
        """
        query = select(Entity).where(Entity.type == entity_type)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Entity.user_id == self.user_id)
        
        result = await self.db.execute(query)
        entities = result.scalars().all()
        
        return [
            {
                "id": e.id,
                "type": e.type,
                "value": e.value,
                "severity": e.severity,
                "metadata": e.meta_data or {},  # Map meta_data back to metadata in API response
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in entities
        ]
    
    async def exists(self, value: str) -> bool:
        """
        Check if a value exists.
        
        Args:
            value: Value to check
            
        Returns:
            True if exists
        """
        query = select(func.count(Entity.id)).where(Entity.value == value)
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(Entity.user_id == self.user_id)
        
        result = await self.db.execute(query)
        count = result.scalar_one()
        return count > 0
    
    # ==================== Graph Operations ====================
    
    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
        metadata: dict = None
    ):
        """
        Add a relationship between entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relation: Relationship type
            weight: Edge weight
            metadata: Additional edge data
        """
        # Get or create graph nodes for source and target
        source_node = await self._get_or_create_graph_node(source_id)
        target_node = await self._get_or_create_graph_node(target_id)
        
        if not source_node or not target_node:
            raise ValueError("Could not create graph nodes for entities")
        
        # Check if edge already exists
        edge_id = f"{source_node.id}-{target_node.id}-{relation}"
        result = await self.db.execute(
            select(GraphEdge).where(GraphEdge.id == edge_id)
        )
        existing_edge = result.scalar_one_or_none()
        
        if existing_edge:
            # Update existing edge
            existing_edge.weight = weight
            existing_edge.meta_data = metadata or {}
        else:
            # Create new edge
            edge = GraphEdge(
                id=edge_id,
                user_id=self.user_id,
                source_id=source_node.id,
                target_id=target_node.id,
                relation=relation,
                weight=weight,
                meta_data=metadata or {}
            )
            self.db.add(edge)
        
        await self.db.commit()
    
    async def _get_or_create_graph_node(self, entity_id: str) -> Optional[GraphNode]:
        """Get or create a graph node for an entity."""
        # First, try to get the entity
        entity = await self.get_entity(entity_id)
        if not entity:
            return None
        
        # Check if graph node exists
        result = await self.db.execute(
            select(GraphNode).where(GraphNode.entity_id == entity_id)
        )
        node = result.scalar_one_or_none()
        
        if node:
            return node
        
        # Create new graph node
        node_id = f"node-{entity_id}"
        node = GraphNode(
            id=node_id,
            user_id=self.user_id,
            entity_id=entity_id,
            label=entity.get("value", entity_id),
            node_type=entity.get("type", "unknown"),
            data=entity
        )
        self.db.add(node)
        await self.db.flush()
        
        return node
    
    async def get_neighbors(self, entity_id: str, depth: int = 1) -> List[str]:
        """
        Get neighboring entity IDs.
        
        Args:
            entity_id: Starting entity
            depth: Maximum depth (currently supports depth=1)
            
        Returns:
            List of neighbor entity IDs
        """
        # Get graph node for entity
        result = await self.db.execute(
            select(GraphNode).where(GraphNode.entity_id == entity_id)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            return []
        
        # Get edges connected to this node
        query = select(GraphEdge).where(
            or_(
                GraphEdge.source_id == node.id,
                GraphEdge.target_id == node.id
            )
        )
        
        # Apply user filter if not admin
        if not self.is_admin:
            query = query.where(GraphEdge.user_id == self.user_id)
        
        result = await self.db.execute(query)
        edges = result.scalars().all()
        
        # Collect neighbor node IDs
        neighbor_node_ids = set()
        for edge in edges:
            if edge.source_id == node.id:
                neighbor_node_ids.add(edge.target_id)
            else:
                neighbor_node_ids.add(edge.source_id)
        
        # Get entity IDs from neighbor nodes
        if neighbor_node_ids:
            node_query = select(GraphNode.entity_id).where(
                GraphNode.id.in_(neighbor_node_ids)
            )
            if not self.is_admin:
                node_query = node_query.where(GraphNode.user_id == self.user_id)
            
            result = await self.db.execute(node_query)
            neighbor_entity_ids = [row[0] for row in result.fetchall() if row[0]]
            return neighbor_entity_ids
        
        return []
    
    async def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """
        Find path between two entities using BFS.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            
        Returns:
            List of entity IDs in path, or None
        """
        # Get graph nodes
        source_result = await self.db.execute(
            select(GraphNode).where(GraphNode.entity_id == source_id)
        )
        source_node = source_result.scalar_one_or_none()
        
        target_result = await self.db.execute(
            select(GraphNode).where(GraphNode.entity_id == target_id)
        )
        target_node = target_result.scalar_one_or_none()
        
        if not source_node or not target_node:
            return None
        
        # BFS to find path
        queue = [(source_node.id, [source_id])]
        visited = {source_node.id}
        
        while queue:
            current_node_id, path = queue.pop(0)
            
            if current_node_id == target_node.id:
                return path
            
            # Get neighbors
            edge_query = select(GraphEdge).where(
                or_(
                    GraphEdge.source_id == current_node_id,
                    GraphEdge.target_id == current_node_id
                )
            )
            if not self.is_admin:
                edge_query = edge_query.where(GraphEdge.user_id == self.user_id)
            
            result = await self.db.execute(edge_query)
            edges = result.scalars().all()
            
            for edge in edges:
                neighbor_id = edge.target_id if edge.source_id == current_node_id else edge.source_id
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    # Get entity ID from node
                    node_result = await self.db.execute(
                        select(GraphNode.entity_id).where(GraphNode.id == neighbor_id)
                    )
                    entity_id_row = node_result.scalar_one_or_none()
                    if entity_id_row and entity_id_row[0]:
                        queue.append((neighbor_id, path + [entity_id_row[0]]))
        
        return None
    
    async def get_graph_data(self) -> dict:
        """
        Get full graph data for visualization.
        
        Returns:
            Dictionary with nodes and edges
        """
        # Get all graph nodes
        node_query = select(GraphNode)
        if not self.is_admin:
            node_query = node_query.where(GraphNode.user_id == self.user_id)
        
        node_result = await self.db.execute(node_query)
        nodes = node_result.scalars().all()
        
        # Get all graph edges
        edge_query = select(GraphEdge)
        if not self.is_admin:
            edge_query = edge_query.where(GraphEdge.user_id == self.user_id)
        
        edge_result = await self.db.execute(edge_query)
        edges = edge_result.scalars().all()
        
        # Build graph structure
        graph_nodes = {}
        graph_edges = {}
        
        for node in nodes:
            graph_nodes[node.id] = {
                "label": node.label,
                "node_type": node.node_type,
                "data": node.data or {},
                "severity": node.data.get("severity", "info") if node.data else "info"
            }
        
        for edge in edges:
            edge_key = edge.id
            graph_edges[edge_key] = {
                "source": edge.source_id,
                "target": edge.target_id,
                "relation": edge.relation,
                "weight": edge.weight,
                "metadata": edge.meta_data or {}  # Map meta_data back to metadata in API response
            }
        
        return {
            "nodes": graph_nodes,
            "edges": graph_edges
        }
    
    # ==================== Statistics ====================
    
    async def stats(self) -> dict:
        """Get storage statistics."""
        # Count entities
        entity_query = select(func.count(Entity.id))
        if not self.is_admin:
            entity_query = entity_query.where(Entity.user_id == self.user_id)
        
        result = await self.db.execute(entity_query)
        entity_count = result.scalar_one()
        
        # Count graph nodes
        node_query = select(func.count(GraphNode.id))
        if not self.is_admin:
            node_query = node_query.where(GraphNode.user_id == self.user_id)
        
        result = await self.db.execute(node_query)
        node_count = result.scalar_one()
        
        # Count graph edges
        edge_query = select(func.count(GraphEdge.id))
        if not self.is_admin:
            edge_query = edge_query.where(GraphEdge.user_id == self.user_id)
        
        result = await self.db.execute(edge_query)
        edge_count = result.scalar_one()
        
        return {
            "entities": entity_count,
            "graph_nodes": node_count,
            "graph_edges": edge_count,
            "storage_backend": "postgresql"
        }

