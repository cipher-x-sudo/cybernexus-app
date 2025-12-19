"""
Graph Routes

Handles graph queries, traversals, and relationship management.
Uses custom Graph DSA implementation with Redis storage.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from enum import Enum
from loguru import logger

from app.core.database.storage import Storage
from app.services.orchestrator import get_orchestrator

router = APIRouter()

# Global storage instance
_storage_instance: Optional[Storage] = None

def get_storage() -> Storage:
    """Get or create global storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = Storage()
    return _storage_instance


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
    min_severity: Optional[str] = None
):
    """Get the full graph data for visualization from Redis storage."""
    try:
        # Get graph data from Storage (which uses Redis)
        storage = get_storage()
        graph_data = storage.get_graph_data()
        
        nodes = []
        edges = []
        
        # Convert graph nodes to GraphNode format
        if "nodes" in graph_data:
            for node_id, node_data in graph_data["nodes"].items():
                # Get entity data if available
                entity = storage.get_entity(node_id)
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
async def get_node(node_id: str):
    """Get a specific node by ID from Redis storage."""
    try:
        # Get entity from storage
        storage = get_storage()
        entity = storage.get_entity(node_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Get graph data to check node metadata
        graph_data = storage.get_graph_data()
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
    direction: str = Query(default="both", regex="^(in|out|both)$")
):
    """Get neighbors of a node up to specified depth from Redis storage."""
    try:
        # Check if node exists
        storage = get_storage()
        entity = storage.get_entity(node_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Node not found")
    
        # Use Storage's get_neighbors method
        neighbor_ids = storage.get_neighbors(node_id, depth=depth)
        
        # Get all neighbor entities
        nodes = []
        edges = []
        visited = {node_id}
        
        # Get starting node
        graph_data = storage.get_graph_data()
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
            
            neighbor_entity = storage.get_entity(neighbor_id)
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
    depth: int = Query(default=2, ge=1, le=5)
):
    """Get focused graph data for a specific finding, showing relationships of affected assets."""
    try:
        # Get finding from orchestrator
        orchestrator = get_orchestrator()
        finding = None
        
        # Try to get from Redis first
        if orchestrator._use_redis and orchestrator.redis:
            try:
                finding_data = orchestrator.redis.get_json(orchestrator.KEY_FINDING.format(finding_id))
                if finding_data:
                    from app.services.orchestrator import Finding, Capability
                    from datetime import datetime
                    finding = Finding(
                        id=finding_data["id"],
                        capability=Capability(finding_data["capability"]),
                        severity=finding_data["severity"],
                        title=finding_data["title"],
                        description=finding_data["description"],
                        evidence=finding_data["evidence"],
                        affected_assets=finding_data["affected_assets"],
                        recommendations=finding_data["recommendations"],
                        discovered_at=datetime.fromisoformat(finding_data["discovered_at"]),
                        risk_score=finding_data["risk_score"],
                        target=finding_data.get("target", "")
                    )
            except Exception as e:
                logger.debug(f"Finding not found in Redis: {e}")
        
        # Fallback to in-memory search
        if not finding:
            for f in orchestrator._all_findings:
                if f.id == finding_id:
                    finding = f
                    break
        
        if not finding:
            # Fallback to full graph if finding not found
            logger.warning(f"Finding {finding_id} not found, returning empty graph")
            return GraphData(nodes=[], edges=[])
        
        # Extract node IDs from finding
        node_ids = []
        
        # Add affected assets (these are entity IDs)
        node_ids.extend(finding.affected_assets)
        
        # Try to map target to entity ID
        if finding.target:
            storage = get_storage()
            # Try to find entity by value (target might be domain/IP)
            graph_data = storage.get_graph_data()
            for node_id, node_data in graph_data.get("nodes", {}).items():
                entity = storage.get_entity(node_id)
                if entity and entity.get("value") == finding.target:
                    if node_id not in node_ids:
                        node_ids.append(node_id)
                    break
            # If not found, try using target as node ID directly
            if finding.target not in node_ids:
                entity = storage.get_entity(finding.target)
                if entity:
                    node_ids.append(finding.target)
        
        if not node_ids:
            # No nodes to show, return empty graph
            logger.warning(f"Finding {finding_id} has no associated nodes")
            return GraphData(nodes=[], edges=[])
        
        # Get neighbors for all affected nodes
        storage = get_storage()
        graph_data = storage.get_graph_data()
        all_node_ids = set(node_ids)
        visited = set()
        nodes = []
        edges = []
        
        # Get all nodes (affected assets + their neighbors)
        for node_id in node_ids:
            if node_id in visited:
                continue
            
            # Get the node itself
            entity = storage.get_entity(node_id)
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
            neighbor_ids = storage.get_neighbors(node_id, depth=depth)
            for neighbor_id in neighbor_ids:
                if neighbor_id not in visited:
                    all_node_ids.add(neighbor_id)
                    visited.add(neighbor_id)
                    
                    neighbor_entity = storage.get_entity(neighbor_id)
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
    algorithm: str = Query(default="bfs", regex="^(bfs|dijkstra)$")
):
    """Find path between two nodes using Redis storage."""
    try:
        if source == target:
            return PathResult(path=[source], total_weight=0, edges=[])
    
        # Use Storage's find_path method
        storage = get_storage()
        path = storage.find_path(source, target)
        
        if not path:
            raise HTTPException(status_code=404, detail="No path found between nodes")
        
        # Get edges for the path
        graph_data = storage.get_graph_data()
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
async def create_edge(edge: GraphEdge):
    """Create a new edge between nodes."""
    sample_edges.append(edge)
    return edge


@router.delete("/edge/{edge_id}")
async def delete_edge(edge_id: str):
    """Delete an edge."""
    for i, edge in enumerate(sample_edges):
        if edge.id == edge_id:
            sample_edges.pop(i)
            return {"message": "Edge deleted successfully"}
    raise HTTPException(status_code=404, detail="Edge not found")


