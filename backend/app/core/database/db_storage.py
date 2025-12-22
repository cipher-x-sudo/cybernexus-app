"""Database storage layer with graph support.

This module provides database-backed storage for entities with graph-based
relationship management using PostgreSQL and custom graph structures.

This module uses the following DSA concepts from app.core.dsa:
- Graph: Entity relationship mapping and graph operations for correlation analysis
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
    def __init__(self, db: AsyncSession, user_id: Optional[str] = None, is_admin: bool = False):
        self.db = db
        self.user_id = user_id
        self.is_admin = is_admin
    
    def _get_user_filter(self):
        if self.is_admin:
            return None
        return Entity.user_id == self.user_id
    
    async def save_entity(self, entity: dict, user_id: Optional[str] = None) -> str:
        entity_id = entity.get("id")
        if not entity_id:
            raise ValueError("Entity must have an 'id' field")
        
        owner_id = user_id or self.user_id
        if not owner_id:
            raise ValueError("user_id must be provided")
        
        result = await self.db.execute(
            select(Entity).where(Entity.id == entity_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            if not self.is_admin and existing.user_id != owner_id:
                raise PermissionError("Cannot update entity owned by another user")
            
            existing.type = entity.get("type", existing.type)
            existing.value = entity.get("value", existing.value)
            existing.severity = entity.get("severity", existing.severity)
            existing.meta_data = entity.get("metadata", existing.meta_data) or {}
        else:
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
        query = select(Entity).where(Entity.id == entity_id)
        
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
            "metadata": entity.meta_data or {},
            "created_at": entity.created_at.isoformat() if entity.created_at else None
        }
    
    async def delete_entity(self, entity_id: str) -> bool:
        query = select(Entity).where(Entity.id == entity_id)
        
        if not self.is_admin:
            query = query.where(Entity.user_id == self.user_id)
        
        result = await self.db.execute(query)
        entity = result.scalar_one_or_none()
        
        if not entity:
            return False
        
        node_result = await self.db.execute(
            select(GraphNode).where(GraphNode.entity_id == entity_id)
        )
        nodes = node_result.scalars().all()
        node_ids = [node.id for node in nodes]
        
        if node_ids:
            await self.db.execute(
                delete(GraphEdge).where(
                    or_(
                        GraphEdge.source_id.in_(node_ids),
                        GraphEdge.target_id.in_(node_ids)
                    )
                )
            )
            await self.db.execute(
                delete(GraphNode).where(GraphNode.entity_id == entity_id)
            )
        
        await self.db.execute(
            delete(Entity).where(Entity.id == entity_id)
        )
        await self.db.commit()
        
        return True
    
    async def search_by_prefix(self, prefix: str, limit: int = 100) -> List[str]:
        query = select(Entity.id).where(Entity.value.ilike(f"{prefix}%"))
        
        if not self.is_admin:
            query = query.where(Entity.user_id == self.user_id)
        
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        return [row[0] for row in result.fetchall()]
    
    async def get_by_type(self, entity_type: str) -> List[dict]:
        query = select(Entity).where(Entity.type == entity_type)
        
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
                "metadata": e.meta_data or {},
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in entities
        ]
    
    async def exists(self, value: str) -> bool:
        query = select(func.count(Entity.id)).where(Entity.value == value)
        
        if not self.is_admin:
            query = query.where(Entity.user_id == self.user_id)
        
        result = await self.db.execute(query)
        count = result.scalar_one()
        return count > 0
    
    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
        metadata: dict = None
    ):
        source_node = await self._get_or_create_graph_node(source_id)
        target_node = await self._get_or_create_graph_node(target_id)
        
        if not source_node or not target_node:
            raise ValueError("Could not create graph nodes for entities")
        
        edge_id = f"{source_node.id}-{target_node.id}-{relation}"
        result = await self.db.execute(
            select(GraphEdge).where(GraphEdge.id == edge_id)
        )
        existing_edge = result.scalar_one_or_none()
        
        if existing_edge:
            existing_edge.weight = weight
            existing_edge.meta_data = metadata or {}
        else:
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
        entity = await self.get_entity(entity_id)
        if not entity:
            return None
        
        result = await self.db.execute(
            select(GraphNode).where(GraphNode.entity_id == entity_id)
        )
        node = result.scalar_one_or_none()
        
        if node:
            return node
        
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
        result = await self.db.execute(
            select(GraphNode).where(GraphNode.entity_id == entity_id)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            return []
        
        query = select(GraphEdge).where(
            or_(
                GraphEdge.source_id == node.id,
                GraphEdge.target_id == node.id
            )
        )
        
        if not self.is_admin:
            query = query.where(GraphEdge.user_id == self.user_id)
        
        result = await self.db.execute(query)
        edges = result.scalars().all()
        
        neighbor_node_ids = set()
        for edge in edges:
            if edge.source_id == node.id:
                neighbor_node_ids.add(edge.target_id)
            else:
                neighbor_node_ids.add(edge.source_id)
        
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
        
        queue = [(source_node.id, [source_id])]
        visited = {source_node.id}
        
        while queue:
            current_node_id, path = queue.pop(0)
            
            if current_node_id == target_node.id:
                return path
            
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
                    node_result = await self.db.execute(
                        select(GraphNode.entity_id).where(GraphNode.id == neighbor_id)
                    )
                    entity_id_row = node_result.scalar_one_or_none()
                    if entity_id_row and entity_id_row[0]:
                        queue.append((neighbor_id, path + [entity_id_row[0]]))
        
        return None
    
    async def get_graph_data(self) -> dict:
        node_query = select(GraphNode)
        if not self.is_admin:
            node_query = node_query.where(GraphNode.user_id == self.user_id)
        
        node_result = await self.db.execute(node_query)
        nodes = node_result.scalars().all()
        
        edge_query = select(GraphEdge)
        if not self.is_admin:
            edge_query = edge_query.where(GraphEdge.user_id == self.user_id)
        
        edge_result = await self.db.execute(edge_query)
        edges = edge_result.scalars().all()
        
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
                "metadata": edge.meta_data or {}
            }
        
        return {
            "nodes": graph_nodes,
            "edges": graph_edges
        }
    
    async def stats(self) -> dict:
        entity_query = select(func.count(Entity.id))
        if not self.is_admin:
            entity_query = entity_query.where(Entity.user_id == self.user_id)
        
        result = await self.db.execute(entity_query)
        entity_count = result.scalar_one()
        
        node_query = select(func.count(GraphNode.id))
        if not self.is_admin:
            node_query = node_query.where(GraphNode.user_id == self.user_id)
        
        result = await self.db.execute(node_query)
        node_count = result.scalar_one()
        
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

