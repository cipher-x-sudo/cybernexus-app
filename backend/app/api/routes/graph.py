"""
Graph Routes

Handles graph queries, traversals, and relationship management.
Uses database-backed storage with user scoping.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from enum import Enum
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_db
from app.core.database.db_storage import DBStorage
from app.api.routes.auth import get_current_active_user, User, is_admin
from app.services.orchestrator import get_orchestrator

router = APIRouter()


class RelationType(str, Enum):
    """Types of relationships between entities."""
    RESOLVES_TO = "resolves_to"
    CONTAINS = "contains"
    COMMUNICATES_WITH = "communicates_with"
    HOSTS = "hosts"
    REGISTERED_BY = "registered_by"
    ASSOCIATED_WITH = "associated_with"
    LEAKED_IN = "leaked_in"
    TARGETS = "targets"
    USES = "uses"
    EXPLOITS = "exploits"


class GraphNode(BaseModel):
    """Graph node representation."""
    id: str
    label: str
    type: str
    severity: str = "info"
    metadata: dict = {}
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class GraphEdge(BaseModel):
    """Graph edge representation."""
    id: str
    source: str
    target: str
    relation: RelationType
    weight: float = 1.0
    metadata: dict = {}


class GraphData(BaseModel):
    """Complete graph data for visualization."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class PathResult(BaseModel):
    """Path between two nodes."""
    path: List[str]
    total_weight: float
    edges: List[GraphEdge]


class ClusterResult(BaseModel):
    """Node cluster."""
    cluster_id: int
    nodes: List[str]
    center: Optional[str] = None


# Graph data will be populated from real DarkWatch site relationships
# No sample data - graph is built dynamically from collected intelligence
sample_nodes = []
sample_edges = []


@router.get("", response_model=GraphData)
async def get_full_graph(
    limit: int = Query(default=1000, le=10000),
    entity_types: Optional[List[str]] = Query(default=None),
    min_severity: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the full graph data for visualization from database storage."""
    try:
        # Get graph data from database storage
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        graph_data = await storage.get_graph_data()
        
        nodes = []
        edges = []
        
        # Convert graph nodes to GraphNode format
        if "nodes" in graph_data:
            for node_id, node_data in graph_data["nodes"].items():
                # Get entity data if available (try to get from entity_id in node data)
                entity_id = node_data.get("data", {}).get("id") if isinstance(node_data.get("data"), dict) else None
                entity = None
                if entity_id:
                    entity = await storage.get_entity(entity_id)
                if entity:
                    severity = entity.get("severity", "info")
                    node_type = entity.get("type", node_data.get("node_type", "unknown"))
                    label = entity.get("value", node_data.get("label", node_id))
                else:
                    severity = node_data.get("severity", "info")
                    node_type = node_data.get("node_type", "unknown")
                    label = node_data.get("label", node_id)
    
                # Apply filters
                if entity_types and node_type not in entity_types:
                    continue
                if min_severity:
                    severity_levels = ["info", "low", "medium", "high", "critical"]
                    if severity_levels.index(severity) < severity_levels.index(min_severity):
                        continue
                
                nodes.append(GraphNode(
                    id=node_id,
                    label=label,
                    type=node_type,
                    severity=severity,
                    metadata=node_data.get("data", {})
                ))
        
        # Convert graph edges to GraphEdge format
        if "edges" in graph_data:
            for edge_key, edge_data in graph_data["edges"].items():
                source = edge_data.get("source")
                target = edge_data.get("target")
                relation = edge_data.get("relation", "associated_with")
                weight = edge_data.get("weight", 1.0)
                
                # Only include edges where both nodes are in our filtered nodes
                node_ids = {n.id for n in nodes}
                if source in node_ids and target in node_ids:
                    edges.append(GraphEdge(
                        id=edge_key,
                        source=source,
                        target=target,
                        relation=RelationType(relation) if hasattr(RelationType, relation.upper().replace("-", "_")) else RelationType.ASSOCIATED_WITH,
                        weight=weight,
                        metadata=edge_data.get("metadata", {})
                    ))
        
        # Limit results
        nodes = nodes[:limit]
        # Filter edges to only include those connecting our limited nodes
        node_ids = {n.id for n in nodes}
        edges = [e for e in edges if e.source in node_ids and e.target in node_ids]
    
        return GraphData(nodes=nodes, edges=edges)
        
    except Exception as e:
        logger.error(f"Error getting graph data: {e}", exc_info=True)
        # Fallback to empty graph
        return GraphData(nodes=[], edges=[])


@router.get("/node/{node_id}", response_model=GraphNode)
async def get_node(
    node_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific node by ID from database storage."""
    try:
        # Get entity from storage
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        entity = await storage.get_entity(node_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Get graph data to check node metadata
        graph_data = await storage.get_graph_data()
        node_data = graph_data.get("nodes", {}).get(node_id, {})
        
        return GraphNode(
            id=node_id,
            label=entity.get("value", node_data.get("label", node_id)),
            type=entity.get("type", node_data.get("node_type", "unknown")),
            severity=entity.get("severity", "info"),
            metadata=entity
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node {node_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving node: {str(e)}")


@router.get("/node/{node_id}/neighbors", response_model=GraphData)
async def get_neighbors(
    node_id: str,
    depth: int = Query(default=1, ge=1, le=5),
    direction: str = Query(default="both", regex="^(in|out|both)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get neighbors of a node up to specified depth from database storage."""
    try:
        # Check if node exists
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        entity = await storage.get_entity(node_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Node not found")
    
        # Use Storage's get_neighbors method
        neighbor_ids = await storage.get_neighbors(node_id, depth=depth)
        
        # Get all neighbor entities
        nodes = []
        edges = []
        visited = {node_id}
        
        # Get starting node
        graph_data = await storage.get_graph_data()
        node_data = graph_data.get("nodes", {}).get(node_id, {})
        nodes.append(GraphNode(
            id=node_id,
            label=entity.get("value", node_data.get("label", node_id)),
            type=entity.get("type", node_data.get("node_type", "unknown")),
            severity=entity.get("severity", "info"),
            metadata=entity
        ))
        
        # Get neighbor nodes
        for neighbor_id in neighbor_ids:
            if neighbor_id in visited:
                continue
            visited.add(neighbor_id)
            
            neighbor_entity = await storage.get_entity(neighbor_id)
            if neighbor_entity:
                neighbor_node_data = graph_data.get("nodes", {}).get(neighbor_id, {})
                nodes.append(GraphNode(
                    id=neighbor_id,
                    label=neighbor_entity.get("value", neighbor_node_data.get("label", neighbor_id)),
                    type=neighbor_entity.get("type", neighbor_node_data.get("node_type", "unknown")),
                    severity=neighbor_entity.get("severity", "info"),
                    metadata=neighbor_entity
                ))
        
        # Get edges between these nodes
        if "edges" in graph_data:
            for edge_key, edge_data in graph_data["edges"].items():
                source = edge_data.get("source")
                target = edge_data.get("target")
                if source in visited and target in visited:
                    relation = edge_data.get("relation", "associated_with")
                    edges.append(GraphEdge(
                        id=edge_key,
                        source=source,
                        target=target,
                        relation=RelationType(relation) if hasattr(RelationType, relation.upper().replace("-", "_")) else RelationType.ASSOCIATED_WITH,
                        weight=edge_data.get("weight", 1.0),
                        metadata=edge_data.get("metadata", {})
                    ))
    
        return GraphData(nodes=nodes, edges=edges)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting neighbors for {node_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving neighbors: {str(e)}")


@router.get("/finding/{finding_id}", response_model=GraphData)
async def get_graph_for_finding(
    finding_id: str,
    depth: int = Query(default=2, ge=1, le=5),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get focused graph data for a specific finding, showing relationships of affected assets."""
    try:
        from urllib.parse import urlparse
        import re
        
        # Get finding from database
        from app.core.database.finding_storage import DBFindingStorage
        finding_storage = DBFindingStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        finding = await finding_storage.get_finding(finding_id)
        
        if not finding:
            # Fallback to full graph if finding not found
            logger.warning(f"Finding {finding_id} not found, returning empty graph")
            return GraphData(nodes=[], edges=[])
        
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        graph_data = await storage.get_graph_data()
        node_ids = []
        
        def extract_domain_or_ip(value: str) -> str:
            """Extract domain or IP from URL or return as-is."""
            if not value:
                return ""
            # Check if it's already an IP
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if re.match(ip_pattern, value):
                return value
            # Try to parse as URL
            try:
                parsed = urlparse(value)
                domain = parsed.netloc or parsed.path.split('/')[0]
                # Remove port if present
                domain = domain.split(':')[0]
                return domain
            except:
                # If parsing fails, assume it's already a domain/IP
                return value
        
        def find_or_create_entity(value: str, entity_type: str = "domain") -> Optional[str]:
            """Find entity by value or create it if not found. Returns entity ID."""
            if not value:
                return None
            
            # First, try to find existing entity by value
            entities_by_type = await storage.get_by_type(entity_type)
            for entity in entities_by_type:
                if entity.get("value") == value:
                    return entity.get("id")
            
            # Also check all entities in graph
            for node_id, node_data in graph_data.get("nodes", {}).items():
                entity_id = node_data.get("data", {}).get("id") if isinstance(node_data.get("data"), dict) else None
                if entity_id:
                    entity = await storage.get_entity(entity_id)
                    if entity and entity.get("value") == value:
                        return entity_id
            
            # If not found, create a new entity
            try:
                from uuid import uuid4
                entity_id = f"{entity_type}-{uuid4().hex[:8]}"
                entity_data = {
                    "id": entity_id,
                    "type": entity_type,
                    "value": value,
                    "severity": finding.severity if finding else "info",
                    "discovered_at": finding.discovered_at.isoformat() if finding else None,
                    "source": "finding_graph"
                }
                await storage.save_entity(entity_data)
                logger.debug(f"Created entity {entity_id} for value {value}")
                return entity_id
            except Exception as e:
                logger.warning(f"Failed to create entity for {value}: {e}")
                return None
        
        # Process affected_assets - they might be URLs, domains, or entity IDs
        for asset in finding.affected_assets:
            if not asset:
                continue
            
            # Try as entity ID first
            entity = await storage.get_entity(asset)
            if entity:
                node_ids.append(asset)
                continue
            
            # Extract domain/IP from URL
            domain_or_ip = extract_domain_or_ip(asset)
            if not domain_or_ip:
                continue
            
            # Determine entity type
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            entity_type = "ip_address" if re.match(ip_pattern, domain_or_ip) else "domain"
            
            # Find or create entity
            entity_id = find_or_create_entity(domain_or_ip, entity_type)
            if entity_id and entity_id not in node_ids:
                node_ids.append(entity_id)
        
        # Process target
        if finding.target:
            target_domain_or_ip = extract_domain_or_ip(finding.target)
            if target_domain_or_ip:
                ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
                entity_type = "ip_address" if re.match(ip_pattern, target_domain_or_ip) else "domain"
                entity_id = find_or_create_entity(target_domain_or_ip, entity_type)
                if entity_id and entity_id not in node_ids:
                    node_ids.append(entity_id)
        
        if not node_ids:
            # No nodes to show, return empty graph
            logger.warning(f"Finding {finding_id} has no associated nodes after processing")
            return GraphData(nodes=[], edges=[])
        
        # Refresh graph data after creating entities
        graph_data = await storage.get_graph_data()
        
        # Add finding as a node and create relationships to affected assets
        finding_node_id = f"finding-{finding_id}"
        all_node_ids = set(node_ids)
        all_node_ids.add(finding_node_id)
        
        # Create finding entity if it doesn't exist
        finding_entity = await storage.get_entity(finding_node_id)
        if not finding_entity:
            finding_entity = {
                "id": finding_node_id,
                "type": "finding",
                "value": finding.title,
                "severity": finding.severity,
                "title": finding.title,
                "description": finding.description,
                "capability": finding.capability.value,
                "risk_score": finding.risk_score,
                "discovered_at": finding.discovered_at.isoformat(),
                "source": "orchestrator"
            }
            await storage.save_entity(finding_entity)
            logger.debug(f"Created finding entity {finding_node_id}")
        
        # Create relationships from finding to affected assets
        for asset_node_id in node_ids:
            try:
                # Check if edge already exists
                edge_exists = False
                if "edges" in graph_data:
                    for edge_key, edge_data in graph_data["edges"].items():
                        if (edge_data.get("source") == finding_node_id and edge_data.get("target") == asset_node_id) or \
                           (edge_data.get("source") == asset_node_id and edge_data.get("target") == finding_node_id):
                            edge_exists = True
                            break
                
                if not edge_exists:
                    await storage.add_relationship(
                        finding_node_id,
                        asset_node_id,
                        relation="targets",
                        weight=1.0
                    )
                    logger.debug(f"Created edge from finding {finding_node_id} to asset {asset_node_id}")
            except Exception as e:
                logger.debug(f"Failed to create edge from finding to asset {asset_node_id}: {e}")
        
        # Refresh graph data after adding edges
        graph_data = await storage.get_graph_data()
        
        # Get neighbors for all affected nodes
        visited = set()
        nodes = []
        edges = []
        
        # Add finding node
        finding_node_data = graph_data.get("nodes", {}).get(finding_node_id, {})
        nodes.append(GraphNode(
            id=finding_node_id,
            label=finding.title,
            type="finding",
            severity=finding.severity,
            metadata={**finding_entity, "is_finding": True}
        ))
        visited.add(finding_node_id)
        
        # Get all nodes (affected assets + their neighbors)
        for node_id in node_ids:
            if node_id in visited:
                continue
            
            # Get the node itself
            entity = await storage.get_entity(node_id)
            if entity:
                node_data = graph_data.get("nodes", {}).get(node_id, {})
                nodes.append(GraphNode(
                    id=node_id,
                    label=entity.get("value", node_data.get("label", node_id)),
                    type=entity.get("type", node_data.get("node_type", "unknown")),
                    severity=entity.get("severity", "info"),
                    metadata={**entity, "is_finding_asset": True}
                ))
                visited.add(node_id)
            
            # Get neighbors
            neighbor_ids = await storage.get_neighbors(node_id, depth=depth)
            for neighbor_id in neighbor_ids:
                if neighbor_id not in visited:
                    all_node_ids.add(neighbor_id)
                    visited.add(neighbor_id)
                    
                    neighbor_entity = await storage.get_entity(neighbor_id)
                    if neighbor_entity:
                        neighbor_node_data = graph_data.get("nodes", {}).get(neighbor_id, {})
                        nodes.append(GraphNode(
                            id=neighbor_id,
                            label=neighbor_entity.get("value", neighbor_node_data.get("label", neighbor_id)),
                            type=neighbor_entity.get("type", neighbor_node_data.get("node_type", "unknown")),
                            severity=neighbor_entity.get("severity", "info"),
                            metadata=neighbor_entity
                        ))
        
        # Get edges between all nodes
        if "edges" in graph_data:
            for edge_key, edge_data in graph_data["edges"].items():
                source = edge_data.get("source")
                target = edge_data.get("target")
                if source in all_node_ids and target in all_node_ids:
                    relation = edge_data.get("relation", "associated_with")
                    edges.append(GraphEdge(
                        id=edge_key,
                        source=source,
                        target=target,
                        relation=RelationType(relation) if hasattr(RelationType, relation.upper().replace("-", "_")) else RelationType.ASSOCIATED_WITH,
                        weight=edge_data.get("weight", 1.0),
                        metadata=edge_data.get("metadata", {})
                    ))
        
        return GraphData(nodes=nodes, edges=edges)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting graph for finding {finding_id}: {e}", exc_info=True)
        # Fallback to empty graph
        return GraphData(nodes=[], edges=[])


@router.get("/path", response_model=PathResult)
async def find_path(
    source: str,
    target: str,
    algorithm: str = Query(default="bfs", regex="^(bfs|dijkstra)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Find path between two nodes using database storage."""
    try:
        if source == target:
            return PathResult(path=[source], total_weight=0, edges=[])
    
        # Use Storage's find_path method
        storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
        path = await storage.find_path(source, target)
        
        if not path:
            raise HTTPException(status_code=404, detail="No path found between nodes")
        
        # Get edges for the path
        graph_data = await storage.get_graph_data()
        edges_list = []
        total_weight = 0
        
        for i in range(len(path) - 1):
            source_id = path[i]
            target_id = path[i + 1]
            
            # Find edge between these nodes
            if "edges" in graph_data:
                for edge_key, edge_data in graph_data["edges"].items():
                    if (edge_data.get("source") == source_id and edge_data.get("target") == target_id) or \
                       (edge_data.get("source") == target_id and edge_data.get("target") == source_id):
                        relation = edge_data.get("relation", "associated_with")
                        weight = edge_data.get("weight", 1.0)
                        edges_list.append(GraphEdge(
                            id=edge_key,
                            source=source_id,
                            target=target_id,
                            relation=RelationType(relation) if hasattr(RelationType, relation.upper().replace("-", "_")) else RelationType.ASSOCIATED_WITH,
                            weight=weight,
                            metadata=edge_data.get("metadata", {})
                        ))
                        total_weight += weight
                        break
        
        return PathResult(path=path, total_weight=total_weight, edges=edges_list)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding path from {source} to {target}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error finding path: {str(e)}")


@router.get("/clusters", response_model=List[ClusterResult])
async def find_clusters(min_size: int = Query(default=2, ge=2)):
    """Find clusters of connected nodes."""
    # Simplified connected components (will use custom Graph DSA)
    adj = {}
    all_nodes = set()
    
    for edge in sample_edges:
        if edge.source not in adj:
            adj[edge.source] = []
        adj[edge.source].append(edge.target)
        if edge.target not in adj:
            adj[edge.target] = []
        adj[edge.target].append(edge.source)
        all_nodes.add(edge.source)
        all_nodes.add(edge.target)
    
    visited = set()
    clusters = []
    cluster_id = 0
    
    for node in all_nodes:
        if node not in visited:
            # BFS to find connected component
            component = []
            queue = [node]
            while queue:
                curr = queue.pop(0)
                if curr not in visited:
                    visited.add(curr)
                    component.append(curr)
                    queue.extend(n for n in adj.get(curr, []) if n not in visited)
            
            if len(component) >= min_size:
                clusters.append(ClusterResult(
                    cluster_id=cluster_id,
                    nodes=component,
                    center=component[0]
                ))
                cluster_id += 1
    
    return clusters


@router.post("/edge", response_model=GraphEdge)
async def create_edge(
    edge: GraphEdge,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new edge between nodes."""
    storage = DBStorage(db, user_id=current_user.id, is_admin=is_admin(current_user))
    await storage.add_relationship(
        source_id=edge.source,
        target_id=edge.target,
        relation=edge.relation.value if isinstance(edge.relation, RelationType) else edge.relation,
        weight=edge.weight,
        metadata=edge.metadata  # Pydantic model uses 'metadata', storage maps to 'meta_data' in DB
    )
    return edge


@router.delete("/edge/{edge_id}")
async def delete_edge(
    edge_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an edge."""
    from app.core.database.models import GraphEdge as GraphEdgeModel
    
    # Find edge
    query = select(GraphEdgeModel).where(GraphEdgeModel.id == edge_id)
    if not is_admin(current_user):
        query = query.where(GraphEdgeModel.user_id == current_user.id)
    
    result = await db.execute(query)
    edge = result.scalar_one_or_none()
    
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    
    await db.delete(edge)
    await db.commit()
    
    return {"message": "Edge deleted successfully"}


