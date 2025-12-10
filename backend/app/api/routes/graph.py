"""
Graph Routes

Handles graph queries, traversals, and relationship management.
Uses custom Graph DSA implementation.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from enum import Enum

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


@router.get("/", response_model=GraphData)
async def get_full_graph(
    limit: int = Query(default=1000, le=10000),
    entity_types: Optional[List[str]] = Query(default=None),
    min_severity: Optional[str] = None
):
    """Get the full graph data for visualization."""
    nodes = sample_nodes.copy()
    edges = sample_edges.copy()
    
    # Apply filters if provided
    if entity_types:
        nodes = [n for n in nodes if n.type in entity_types]
        node_ids = {n.id for n in nodes}
        edges = [e for e in edges if e.source in node_ids and e.target in node_ids]
    
    return GraphData(nodes=nodes[:limit], edges=edges)


@router.get("/node/{node_id}", response_model=GraphNode)
async def get_node(node_id: str):
    """Get a specific node by ID."""
    for node in sample_nodes:
        if node.id == node_id:
            return node
    raise HTTPException(status_code=404, detail="Node not found")


@router.get("/node/{node_id}/neighbors", response_model=GraphData)
async def get_neighbors(
    node_id: str,
    depth: int = Query(default=1, ge=1, le=5),
    direction: str = Query(default="both", regex="^(in|out|both)$")
):
    """Get neighbors of a node up to specified depth."""
    # Find the starting node
    start_node = None
    for node in sample_nodes:
        if node.id == node_id:
            start_node = node
            break
    
    if not start_node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # BFS to find neighbors (simplified - will use custom Graph DSA)
    visited_ids = {node_id}
    result_nodes = [start_node]
    result_edges = []
    
    current_layer = [node_id]
    for _ in range(depth):
        next_layer = []
        for curr_id in current_layer:
            for edge in sample_edges:
                neighbor_id = None
                if direction in ["out", "both"] and edge.source == curr_id:
                    neighbor_id = edge.target
                if direction in ["in", "both"] and edge.target == curr_id:
                    neighbor_id = edge.source
                
                if neighbor_id and neighbor_id not in visited_ids:
                    visited_ids.add(neighbor_id)
                    next_layer.append(neighbor_id)
                    result_edges.append(edge)
                    
                    for node in sample_nodes:
                        if node.id == neighbor_id:
                            result_nodes.append(node)
                            break
        
        current_layer = next_layer
    
    return GraphData(nodes=result_nodes, edges=result_edges)


@router.get("/path", response_model=PathResult)
async def find_path(
    source: str,
    target: str,
    algorithm: str = Query(default="bfs", regex="^(bfs|dijkstra)$")
):
    """Find path between two nodes."""
    # Simplified BFS path finding (will use custom Graph DSA)
    if source == target:
        return PathResult(path=[source], total_weight=0, edges=[])
    
    # Build adjacency list
    adj = {}
    for edge in sample_edges:
        if edge.source not in adj:
            adj[edge.source] = []
        adj[edge.source].append((edge.target, edge))
        if edge.target not in adj:
            adj[edge.target] = []
        adj[edge.target].append((edge.source, edge))
    
    # BFS
    from collections import deque
    queue = deque([(source, [source], [], 0)])
    visited = {source}
    
    while queue:
        node, path, edges, weight = queue.popleft()
        
        if node == target:
            return PathResult(path=path, total_weight=weight, edges=edges)
        
        for neighbor, edge in adj.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((
                    neighbor,
                    path + [neighbor],
                    edges + [edge],
                    weight + edge.weight
                ))
    
    raise HTTPException(status_code=404, detail="No path found between nodes")


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


