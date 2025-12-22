"""Threat correlation engine.

This module provides entity correlation and relationship analysis using graph-based
algorithms to identify connections between security entities and threats.

This module uses the following DSA concepts from app.core.dsa:
- Graph: Entity relationship mapping with BFS/DFS traversal for correlation discovery
- HashMap: Entity attribute storage and correlation cache for O(1) lookups
- AVLTree: Timestamp-based correlation indexing for efficient range queries
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from app.core.dsa import Graph, HashMap, AVLTree


class Correlator:
    def __init__(self, graph: Graph = None):
        self.graph = graph or Graph(directed=True)
        self._entity_attributes = HashMap()
        self._correlation_cache = HashMap()
    
    def add_entity(self, entity_id: str, entity_type: str, 
                   attributes: Dict[str, Any] = None):
        self.graph.add_node(entity_id, label=entity_id, node_type=entity_type)
        self._entity_attributes.put(entity_id, attributes or {})
    
    def add_relationship(self, source: str, target: str, 
                        relation: str, confidence: float = 1.0):
        self.graph.add_edge(source, target, weight=confidence, relation=relation)
    
    def find_correlations(self, entity_id: str, depth: int = 2) -> List[Dict[str, Any]]:
        if entity_id not in self.graph:
            return []
        
        correlations = []
        visited = {entity_id}
        current_depth = [(entity_id, 0, 1.0)]
        
        while current_depth:
            next_depth = []
            
            for node_id, d, score in current_depth:
                if d >= depth:
                    continue
                
                node = self.graph.get_node(node_id)
                if not node:
                    continue
                
                for edge in node.edges:
                    if edge.target not in visited:
                        visited.add(edge.target)
                        new_score = score * edge.weight
                        
                        target_node = self.graph.get_node(edge.target)
                        correlations.append({
                            "entity_id": edge.target,
                            "entity_type": target_node.node_type if target_node else "unknown",
                            "relation": edge.relation,
                            "depth": d + 1,
                            "correlation_score": new_score
                        })
                        
                        next_depth.append((edge.target, d + 1, new_score))
            
            current_depth = next_depth
        

        correlations.sort(key=lambda x: x["correlation_score"], reverse=True)
        return correlations
    
    def find_common_connections(self, entity_ids: List[str]) -> List[str]:
        
        if not entity_ids:
            return []
        

        neighbor_sets = []
        for entity_id in entity_ids:
            neighbors = self.graph.get_neighbors(entity_id, depth=1)
            neighbor_sets.append(neighbors)
        

        common = neighbor_sets[0]
        for ns in neighbor_sets[1:]:
            common = common.intersection(ns)
        
        return list(common - set(entity_ids))
    
    def find_shortest_path(self, source: str, target: str) -> Optional[List[Dict[str, Any]]]:
        
        result = self.graph.get_path(source, target)
        if not result:
            return None
        
        path, total_weight = result
        path_details = []
        
        for i, node_id in enumerate(path):
            node = self.graph.get_node(node_id)
            detail = {
                "entity_id": node_id,
                "entity_type": node.node_type if node else "unknown",
                "position": i
            }
            

            if i < len(path) - 1:
                edge = self.graph.get_edge(node_id, path[i + 1])
                if edge:
                    detail["relation_to_next"] = edge.relation
                    detail["confidence"] = edge.weight
            
            path_details.append(detail)
        
        return path_details
    
    def find_clusters(self, min_size: int = 3) -> List[Dict[str, Any]]:
        
        components = self.graph.connected_components()
        
        clusters = []
        for i, component in enumerate(components):
            if len(component) >= min_size:

                types = defaultdict(int)
                for entity_id in component:
                    node = self.graph.get_node(entity_id)
                    if node:
                        types[node.node_type] += 1
                
                clusters.append({
                    "cluster_id": i,
                    "size": len(component),
                    "entities": list(component),
                    "type_distribution": dict(types)
                })
        
        return clusters
    
    def identify_attack_patterns(self) -> List[Dict[str, Any]]:
        
        patterns = []
        

        for node in self.graph:
            in_degree, out_degree = self.graph.get_degree(node.id)
            total_degree = in_degree + out_degree
            
            if total_degree > 5:
                patterns.append({
                    "type": "high_connectivity",
                    "entity_id": node.id,
                    "entity_type": node.node_type,
                    "in_degree": in_degree,
                    "out_degree": out_degree,
                    "significance": "Highly connected node, potential C2 or key infrastructure"
                })
        

        actors = self.graph.get_nodes_by_type("actor")
        for actor in actors:

            for edge in actor.edges:
                if edge.relation == "uses":
                    malware_node = self.graph.get_node(edge.target)
                    if malware_node and malware_node.node_type == "malware":

                        for malware_edge in malware_node.edges:
                            if malware_edge.relation == "targets":
                                patterns.append({
                                    "type": "attack_chain",
                                    "actor": actor.id,
                                    "malware": malware_node.id,
                                    "target": malware_edge.target,
                                    "significance": "Complete attack chain identified"
                                })
        
        return patterns
    
    def calculate_risk_score(self, entity_id: str) -> float:
        
        if entity_id not in self.graph:
            return 0.0
        
        score = 0.0
        

        in_degree, out_degree = self.graph.get_degree(entity_id)
        connectivity_score = min(30, (in_degree + out_degree) * 3)
        score += connectivity_score
        

        node = self.graph.get_node(entity_id)
        high_risk_types = {"malware", "actor", "cve"}
        
        for edge in node.edges:
            neighbor = self.graph.get_node(edge.target)
            if neighbor and neighbor.node_type in high_risk_types:
                score += 20
        

        patterns = self.identify_attack_patterns()
        for pattern in patterns:
            if pattern.get("entity_id") == entity_id or \
               entity_id in [pattern.get("actor"), pattern.get("malware"), pattern.get("target")]:
                score += 30
                break
        
        return min(100, score)


