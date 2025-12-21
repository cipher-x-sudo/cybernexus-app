from typing import Any, Dict, List, Optional, Set, Tuple, Generator
from collections import deque
from dataclasses import dataclass, field
import json


@dataclass
class GraphEdge:
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
    id: str
    label: str
    node_type: str
    data: Dict[str, Any] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    
    def add_edge(self, target: str, weight: float = 1.0, relation: str = "connected", metadata: dict = None):
        edge = GraphEdge(target=target, weight=weight, relation=relation, metadata=metadata or {})
        self.edges.append(edge)
        return edge
    
    def remove_edge(self, target: str) -> bool:
        for i, edge in enumerate(self.edges):
            if edge.target == target:
                self.edges.pop(i)
                return True
        return False
    
    def get_neighbors(self) -> List[str]:
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
    
    def __init__(self, directed: bool = True):
        self.directed = directed
        self.nodes: Dict[str, GraphNode] = {}
        self._node_count = 0
        self._edge_count = 0
    
    def __len__(self) -> int:
        return self._node_count
    
    def __contains__(self, node_id: str) -> bool:
        return node_id in self.nodes
    
    def __iter__(self) -> Generator[GraphNode, None, None]:
        yield from self.nodes.values()
    
    def add_node(self, node_id: str, label: str = None, node_type: str = "default", data: dict = None) -> GraphNode:
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
        return self.nodes.get(node_id)
    
    def remove_node(self, node_id: str) -> bool:
        if node_id not in self.nodes:
            return False
        
        for node in self.nodes.values():
            edges_to_remove = [e for e in node.edges if e.target == node_id]
            for edge in edges_to_remove:
                node.edges.remove(edge)
                self._edge_count -= 1
        
        node = self.nodes[node_id]
        self._edge_count -= len(node.edges)
        del self.nodes[node_id]
        self._node_count -= 1
        return True
    
    def get_nodes_by_type(self, node_type: str) -> List[GraphNode]:
        return [node for node in self.nodes.values() if node.node_type == node_type]
    
    def add_edge(self, source: str, target: str, weight: float = 1.0, 
                 relation: str = "connected", metadata: dict = None) -> bool:
        if source not in self.nodes:
            self.add_node(source)
        if target not in self.nodes:
            self.add_node(target)
        
        source_node = self.nodes[source]
        
        for edge in source_node.edges:
            if edge.target == target:
                edge.weight = weight
                edge.relation = relation
                edge.metadata.update(metadata or {})
                return True
        
        source_node.add_edge(target, weight, relation, metadata)
        self._edge_count += 1
        
        if not self.directed:
            target_node = self.nodes[target]
            target_node.add_edge(source, weight, relation, metadata)
            self._edge_count += 1
        
        return True
    
    def remove_edge(self, source: str, target: str) -> bool:
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
        if source not in self.nodes:
            return False
        return any(edge.target == target for edge in self.nodes[source].edges)
    
    def get_edge(self, source: str, target: str) -> Optional[GraphEdge]:
        if source not in self.nodes:
            return None
        for edge in self.nodes[source].edges:
            if edge.target == target:
                return edge
        return None
    
    def bfs(self, start: str) -> Generator[GraphNode, None, None]:
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
            
            for edge in reversed(node.edges):
                if edge.target not in visited:
                    stack.append(edge.target)
    
    def get_neighbors(self, node_id: str, depth: int = 1) -> Set[str]:
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
    
    def shortest_path_bfs(self, start: str, end: str) -> Optional[List[str]]:
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
        import heapq
        
        if start not in self.nodes:
            return {}, {}
        
        distances = {node_id: float('inf') for node_id in self.nodes}
        distances[start] = 0
        predecessors = {}
        
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
        distances, predecessors = self.dijkstra(start, end)
        
        if end not in predecessors and end != start:
            return None
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = predecessors.get(current)
        
        path.reverse()
        return path, distances.get(end, 0)
    
    def connected_components(self) -> List[Set[str]]:
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
                    
                    if self.directed:
                        for other_node in self.nodes.values():
                            for edge in other_node.edges:
                                if edge.target == current and other_node.id not in visited:
                                    stack.append(other_node.id)
                
                components.append(component)
        
        return components
    
    def has_cycle(self) -> bool:
        if not self.directed:
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
        if node_id not in self.nodes:
            return (0, 0)
        
        out_degree = len(self.nodes[node_id].edges)
        in_degree = sum(1 for node in self.nodes.values() 
                       for edge in node.edges if edge.target == node_id)
        
        return (in_degree, out_degree)
    
    def to_dict(self) -> dict:
        return {
            "directed": self.directed,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Graph":
        graph = cls(directed=data.get("directed", True))
        
        for node_id, node_data in data.get("nodes", {}).items():
            node = GraphNode.from_dict(node_data)
            graph.nodes[node_id] = node
            graph._node_count += 1
            graph._edge_count += len(node.edges)
        
        return graph
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Graph":
        return cls.from_dict(json.loads(json_str))
    
    @property
    def node_count(self) -> int:
        return self._node_count
    
    @property
    def edge_count(self) -> int:
        return self._edge_count
    
    def stats(self) -> dict:
        return {
            "nodes": self._node_count,
            "edges": self._edge_count,
            "directed": self.directed,
            "density": self._edge_count / (self._node_count * (self._node_count - 1)) if self._node_count > 1 else 0,
            "components": len(self.connected_components()),
            "has_cycle": self.has_cycle()
        }


