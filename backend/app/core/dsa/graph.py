"""
Custom Graph Implementation

Adjacency List-based Graph for representing entity relationships in CyberNexus.
Supports directed and undirected graphs, weighted edges, and various traversal algorithms.

Used for:
- Entity relationship mapping (domains, IPs, emails, etc.)
- Threat actor infrastructure correlation
- Attack path visualization
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Generator
from collections import deque
from dataclasses import dataclass, field
import json


@dataclass
class GraphEdge:
    """Represents an edge in the graph."""
    target: str
    weight: float = 1.0
    relation: str = "connected"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "weight": self.weight,
            "relation": self.relation,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GraphEdge":
        return cls(
            target=data["target"],
            weight=data.get("weight", 1.0),
            relation=data.get("relation", "connected"),
            metadata=data.get("metadata", {})
        )


@dataclass
class GraphNode:
    """Represents a node in the graph."""
    id: str
    label: str
    node_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    
    def add_edge(self, target: str, weight: float = 1.0, relation: str = "connected", metadata: dict = None):
        """Add an edge from this node to target."""
        edge = GraphEdge(target=target, weight=weight, relation=relation, metadata=metadata or {})
        self.edges.append(edge)
        return edge
    
    def remove_edge(self, target: str) -> bool:
        """Remove edge to target. Returns True if edge was found and removed."""
        for i, edge in enumerate(self.edges):
            if edge.target == target:
                self.edges.pop(i)
                return True
        return False
    
    def get_neighbors(self) -> List[str]:
        """Get all neighbor node IDs."""
        return [edge.target for edge in self.edges]
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "node_type": self.node_type,
            "data": self.data,
            "edges": [e.to_dict() for e in self.edges]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GraphNode":
        node = cls(
            id=data["id"],
            label=data["label"],
            node_type=data["node_type"],
            data=data.get("data", {})
        )
        node.edges = [GraphEdge.from_dict(e) for e in data.get("edges", [])]
        return node


class Graph:
    """
    Custom Graph implementation using adjacency list.
    
    Features:
    - Directed and undirected graph support
    - Weighted edges with relationship types
    - BFS and DFS traversals
    - Shortest path (Dijkstra, BFS)
    - Connected components detection
    - Cycle detection
    - Serialization/deserialization
    """
    
    def __init__(self, directed: bool = True):
        """Initialize graph.
        
        Args:
            directed: If True, creates a directed graph. Otherwise, undirected.
        """
        self.directed = directed
        self.nodes: Dict[str, GraphNode] = {}
        self._node_count = 0
        self._edge_count = 0
    
    def __len__(self) -> int:
        """Return number of nodes."""
        return self._node_count
    
    def __contains__(self, node_id: str) -> bool:
        """Check if node exists in graph."""
        return node_id in self.nodes
    
    def __iter__(self) -> Generator[GraphNode, None, None]:
        """Iterate over all nodes."""
        yield from self.nodes.values()
    
    # ==================== Node Operations ====================
    
    def add_node(self, node_id: str, label: str = None, node_type: str = "default", data: dict = None) -> GraphNode:
        """Add a node to the graph.
        
        Args:
            node_id: Unique identifier for the node
            label: Display label for the node
            node_type: Type classification (domain, ip, email, etc.)
            data: Additional metadata
            
        Returns:
            The created GraphNode
        """
        if node_id in self.nodes:
            return self.nodes[node_id]
        
        node = GraphNode(
            id=node_id,
            label=label or node_id,
            node_type=node_type,
            data=data or {}
        )
        self.nodes[node_id] = node
        self._node_count += 1
        return node
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges."""
        if node_id not in self.nodes:
            return False
        
        # Remove all edges pointing to this node
        for node in self.nodes.values():
            edges_to_remove = [e for e in node.edges if e.target == node_id]
            for edge in edges_to_remove:
                node.edges.remove(edge)
                self._edge_count -= 1
        
        # Remove the node itself (and its outgoing edges)
        node = self.nodes[node_id]
        self._edge_count -= len(node.edges)
        del self.nodes[node_id]
        self._node_count -= 1
        return True
    
    def get_nodes_by_type(self, node_type: str) -> List[GraphNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes.values() if node.node_type == node_type]
    
    # ==================== Edge Operations ====================
    
    def add_edge(self, source: str, target: str, weight: float = 1.0, 
                 relation: str = "connected", metadata: dict = None) -> bool:
        """Add an edge between two nodes.
        
        Args:
            source: Source node ID
            target: Target node ID
            weight: Edge weight (default 1.0)
            relation: Relationship type
            metadata: Additional edge data
            
        Returns:
            True if edge was added successfully
        """
        # Create nodes if they don't exist
        if source not in self.nodes:
            self.add_node(source)
        if target not in self.nodes:
            self.add_node(target)
        
        source_node = self.nodes[source]
        
        # Check if edge already exists
        for edge in source_node.edges:
            if edge.target == target:
                # Update existing edge
                edge.weight = weight
                edge.relation = relation
                edge.metadata.update(metadata or {})
                return True
        
        # Add new edge
        source_node.add_edge(target, weight, relation, metadata)
        self._edge_count += 1
        
        # If undirected, add reverse edge
        if not self.directed:
            target_node = self.nodes[target]
            target_node.add_edge(source, weight, relation, metadata)
            self._edge_count += 1
        
        return True
    
    def remove_edge(self, source: str, target: str) -> bool:
        """Remove an edge between two nodes."""
        if source not in self.nodes:
            return False
        
        source_node = self.nodes[source]
        if source_node.remove_edge(target):
            self._edge_count -= 1
            
            if not self.directed:
                target_node = self.nodes.get(target)
                if target_node and target_node.remove_edge(source):
                    self._edge_count -= 1
            
            return True
        return False
    
    def has_edge(self, source: str, target: str) -> bool:
        """Check if an edge exists."""
        if source not in self.nodes:
            return False
        return any(edge.target == target for edge in self.nodes[source].edges)
    
    def get_edge(self, source: str, target: str) -> Optional[GraphEdge]:
        """Get edge between two nodes."""
        if source not in self.nodes:
            return None
        for edge in self.nodes[source].edges:
            if edge.target == target:
                return edge
        return None
    
    # ==================== Traversal Algorithms ====================
    
    def bfs(self, start: str) -> Generator[GraphNode, None, None]:
        """Breadth-First Search traversal.
        
        Args:
            start: Starting node ID
            
        Yields:
            Nodes in BFS order
        """
        if start not in self.nodes:
            return
        
        visited = {start}
        queue = deque([start])
        
        while queue:
            node_id = queue.popleft()
            node = self.nodes[node_id]
            yield node
            
            for edge in node.edges:
                if edge.target not in visited:
                    visited.add(edge.target)
                    queue.append(edge.target)
    
    def dfs(self, start: str) -> Generator[GraphNode, None, None]:
        """Depth-First Search traversal (iterative).
        
        Args:
            start: Starting node ID
            
        Yields:
            Nodes in DFS order
        """
        if start not in self.nodes:
            return
        
        visited = set()
        stack = [start]
        
        while stack:
            node_id = stack.pop()
            if node_id in visited:
                continue
            
            visited.add(node_id)
            node = self.nodes[node_id]
            yield node
            
            # Add neighbors in reverse order to maintain consistent ordering
            for edge in reversed(node.edges):
                if edge.target not in visited:
                    stack.append(edge.target)
    
    def get_neighbors(self, node_id: str, depth: int = 1) -> Set[str]:
        """Get all neighbors up to specified depth.
        
        Args:
            node_id: Starting node
            depth: Maximum depth to traverse
            
        Returns:
            Set of neighbor node IDs
        """
        if node_id not in self.nodes:
            return set()
        
        neighbors = set()
        current_layer = {node_id}
        
        for _ in range(depth):
            next_layer = set()
            for current_id in current_layer:
                node = self.nodes.get(current_id)
                if node:
                    for edge in node.edges:
                        if edge.target != node_id:
                            neighbors.add(edge.target)
                            next_layer.add(edge.target)
            current_layer = next_layer
        
        return neighbors
    
    # ==================== Path Finding ====================
    
    def shortest_path_bfs(self, start: str, end: str) -> Optional[List[str]]:
        """Find shortest path using BFS (unweighted).
        
        Args:
            start: Starting node ID
            end: Target node ID
            
        Returns:
            List of node IDs in path, or None if no path exists
        """
        if start not in self.nodes or end not in self.nodes:
            return None
        
        if start == end:
            return [start]
        
        visited = {start}
        queue = deque([(start, [start])])
        
        while queue:
            node_id, path = queue.popleft()
            node = self.nodes[node_id]
            
            for edge in node.edges:
                if edge.target == end:
                    return path + [end]
                
                if edge.target not in visited:
                    visited.add(edge.target)
                    queue.append((edge.target, path + [edge.target]))
        
        return None
    
    def dijkstra(self, start: str, end: str = None) -> Tuple[Dict[str, float], Dict[str, str]]:
        """Dijkstra's algorithm for shortest weighted paths.
        
        Args:
            start: Starting node ID
            end: Optional target node (if specified, stops early when found)
            
        Returns:
            Tuple of (distances dict, predecessors dict)
        """
        import heapq
        
        if start not in self.nodes:
            return {}, {}
        
        distances = {node_id: float('inf') for node_id in self.nodes}
        distances[start] = 0
        predecessors = {}
        
        # Priority queue: (distance, node_id)
        pq = [(0, start)]
        visited = set()
        
        while pq:
            current_dist, current_id = heapq.heappop(pq)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if end and current_id == end:
                break
            
            node = self.nodes[current_id]
            for edge in node.edges:
                if edge.target not in visited:
                    new_dist = current_dist + edge.weight
                    if new_dist < distances[edge.target]:
                        distances[edge.target] = new_dist
                        predecessors[edge.target] = current_id
                        heapq.heappush(pq, (new_dist, edge.target))
        
        return distances, predecessors
    
    def get_path(self, start: str, end: str) -> Optional[Tuple[List[str], float]]:
        """Get shortest weighted path between two nodes.
        
        Returns:
            Tuple of (path list, total weight) or None if no path
        """
        distances, predecessors = self.dijkstra(start, end)
        
        if end not in predecessors and end != start:
            return None
        
        # Reconstruct path
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = predecessors.get(current)
        
        path.reverse()
        return path, distances.get(end, 0)
    
    # ==================== Graph Analysis ====================
    
    def connected_components(self) -> List[Set[str]]:
        """Find all connected components in the graph.
        
        Returns:
            List of sets, each containing node IDs in a component
        """
        visited = set()
        components = []
        
        for node_id in self.nodes:
            if node_id not in visited:
                component = set()
                stack = [node_id]
                
                while stack:
                    current = stack.pop()
                    if current in visited:
                        continue
                    
                    visited.add(current)
                    component.add(current)
                    
                    node = self.nodes[current]
                    for edge in node.edges:
                        if edge.target not in visited:
                            stack.append(edge.target)
                    
                    # For undirected analysis, also check incoming edges
                    if self.directed:
                        for other_node in self.nodes.values():
                            for edge in other_node.edges:
                                if edge.target == current and other_node.id not in visited:
                                    stack.append(other_node.id)
                
                components.append(component)
        
        return components
    
    def has_cycle(self) -> bool:
        """Check if the graph contains a cycle."""
        if not self.directed:
            # For undirected graphs, use DFS with parent tracking
            visited = set()
            
            def dfs_cycle(node_id: str, parent: str) -> bool:
                visited.add(node_id)
                node = self.nodes[node_id]
                
                for edge in node.edges:
                    if edge.target not in visited:
                        if dfs_cycle(edge.target, node_id):
                            return True
                    elif edge.target != parent:
                        return True
                
                return False
            
            for node_id in self.nodes:
                if node_id not in visited:
                    if dfs_cycle(node_id, None):
                        return True
            
            return False
        else:
            # For directed graphs, use color-based DFS
            WHITE, GRAY, BLACK = 0, 1, 2
            colors = {node_id: WHITE for node_id in self.nodes}
            
            def dfs_cycle(node_id: str) -> bool:
                colors[node_id] = GRAY
                node = self.nodes[node_id]
                
                for edge in node.edges:
                    if colors[edge.target] == GRAY:
                        return True
                    if colors[edge.target] == WHITE and dfs_cycle(edge.target):
                        return True
                
                colors[node_id] = BLACK
                return False
            
            for node_id in self.nodes:
                if colors[node_id] == WHITE:
                    if dfs_cycle(node_id):
                        return True
            
            return False
    
    def get_degree(self, node_id: str) -> Tuple[int, int]:
        """Get in-degree and out-degree of a node.
        
        Returns:
            Tuple of (in_degree, out_degree)
        """
        if node_id not in self.nodes:
            return (0, 0)
        
        out_degree = len(self.nodes[node_id].edges)
        in_degree = sum(1 for node in self.nodes.values() 
                       for edge in node.edges if edge.target == node_id)
        
        return (in_degree, out_degree)
    
    # ==================== Serialization ====================
    
    def to_dict(self) -> dict:
        """Serialize graph to dictionary."""
        return {
            "directed": self.directed,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Graph":
        """Deserialize graph from dictionary."""
        graph = cls(directed=data.get("directed", True))
        
        for node_id, node_data in data.get("nodes", {}).items():
            node = GraphNode.from_dict(node_data)
            graph.nodes[node_id] = node
            graph._node_count += 1
            graph._edge_count += len(node.edges)
        
        return graph
    
    def to_json(self) -> str:
        """Serialize graph to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Graph":
        """Deserialize graph from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    # ==================== Statistics ====================
    
    @property
    def node_count(self) -> int:
        """Get number of nodes."""
        return self._node_count
    
    @property
    def edge_count(self) -> int:
        """Get number of edges."""
        return self._edge_count
    
    def stats(self) -> dict:
        """Get graph statistics."""
        return {
            "nodes": self._node_count,
            "edges": self._edge_count,
            "directed": self.directed,
            "density": self._edge_count / (self._node_count * (self._node_count - 1)) if self._node_count > 1 else 0,
            "components": len(self.connected_components()),
            "has_cycle": self.has_cycle()
        }


