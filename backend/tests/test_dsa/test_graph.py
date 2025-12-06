"""
Tests for Graph DSA Implementation
"""

import pytest
from app.core.dsa.graph import Graph, GraphNode, GraphEdge


class TestGraph:
    """Test suite for Graph data structure."""
    
    def test_create_empty_graph(self):
        """Test creating an empty graph."""
        g = Graph()
        assert len(g) == 0
        assert g.directed == True
    
    def test_create_undirected_graph(self):
        """Test creating an undirected graph."""
        g = Graph(directed=False)
        assert g.directed == False
    
    def test_add_node(self):
        """Test adding nodes."""
        g = Graph()
        node = g.add_node("n1", label="Node 1", node_type="domain")
        
        assert len(g) == 1
        assert "n1" in g
        assert node.label == "Node 1"
        assert node.node_type == "domain"
    
    def test_add_duplicate_node(self):
        """Test adding duplicate node returns existing."""
        g = Graph()
        n1 = g.add_node("n1", label="Original")
        n2 = g.add_node("n1", label="Duplicate")
        
        assert len(g) == 1
        assert n1 is n2
    
    def test_get_node(self):
        """Test getting a node by ID."""
        g = Graph()
        g.add_node("n1", label="Node 1")
        
        node = g.get_node("n1")
        assert node is not None
        assert node.id == "n1"
        
        missing = g.get_node("n2")
        assert missing is None
    
    def test_remove_node(self):
        """Test removing a node."""
        g = Graph()
        g.add_node("n1")
        g.add_node("n2")
        g.add_edge("n1", "n2")
        
        assert g.remove_node("n1")
        assert len(g) == 1
        assert "n1" not in g
    
    def test_add_edge(self):
        """Test adding edges."""
        g = Graph()
        g.add_node("n1")
        g.add_node("n2")
        
        g.add_edge("n1", "n2", weight=0.5, relation="resolves_to")
        
        assert g.has_edge("n1", "n2")
        edge = g.get_edge("n1", "n2")
        assert edge.weight == 0.5
        assert edge.relation == "resolves_to"
    
    def test_add_edge_creates_nodes(self):
        """Test that adding edge auto-creates nodes."""
        g = Graph()
        g.add_edge("n1", "n2")
        
        assert "n1" in g
        assert "n2" in g
        assert g.has_edge("n1", "n2")
    
    def test_undirected_edge(self):
        """Test edges in undirected graph."""
        g = Graph(directed=False)
        g.add_edge("n1", "n2")
        
        assert g.has_edge("n1", "n2")
        assert g.has_edge("n2", "n1")
    
    def test_remove_edge(self):
        """Test removing an edge."""
        g = Graph()
        g.add_edge("n1", "n2")
        
        assert g.remove_edge("n1", "n2")
        assert not g.has_edge("n1", "n2")
    
    def test_bfs_traversal(self):
        """Test BFS traversal."""
        g = Graph()
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        g.add_edge("b", "d")
        g.add_edge("c", "d")
        
        visited = [node.id for node in g.bfs("a")]
        
        assert visited[0] == "a"
        assert set(visited) == {"a", "b", "c", "d"}
    
    def test_dfs_traversal(self):
        """Test DFS traversal."""
        g = Graph()
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        g.add_edge("b", "d")
        
        visited = [node.id for node in g.dfs("a")]
        
        assert visited[0] == "a"
        assert set(visited) == {"a", "b", "c", "d"}
    
    def test_get_neighbors(self):
        """Test getting neighbors."""
        g = Graph()
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        g.add_edge("b", "d")
        
        neighbors = g.get_neighbors("a", depth=1)
        assert neighbors == {"b", "c"}
        
        neighbors_depth2 = g.get_neighbors("a", depth=2)
        assert neighbors_depth2 == {"b", "c", "d"}
    
    def test_shortest_path_bfs(self):
        """Test BFS shortest path."""
        g = Graph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("a", "d")
        g.add_edge("d", "c")
        
        path = g.shortest_path_bfs("a", "c")
        
        assert path is not None
        assert path[0] == "a"
        assert path[-1] == "c"
        assert len(path) == 3  # a -> b -> c or a -> d -> c
    
    def test_dijkstra(self):
        """Test Dijkstra's algorithm."""
        g = Graph()
        g.add_edge("a", "b", weight=1)
        g.add_edge("b", "c", weight=2)
        g.add_edge("a", "c", weight=5)
        
        distances, _ = g.dijkstra("a")
        
        assert distances["a"] == 0
        assert distances["b"] == 1
        assert distances["c"] == 3  # a -> b -> c is shorter than a -> c
    
    def test_get_path(self):
        """Test get_path with weighted edges."""
        g = Graph()
        g.add_edge("a", "b", weight=1)
        g.add_edge("b", "c", weight=2)
        g.add_edge("a", "c", weight=10)
        
        result = g.get_path("a", "c")
        
        assert result is not None
        path, weight = result
        assert path == ["a", "b", "c"]
        assert weight == 3
    
    def test_connected_components(self):
        """Test finding connected components."""
        g = Graph(directed=False)
        g.add_edge("a", "b")
        g.add_edge("c", "d")
        
        components = g.connected_components()
        
        assert len(components) == 2
    
    def test_has_cycle_directed(self):
        """Test cycle detection in directed graph."""
        g = Graph(directed=True)
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        
        assert not g.has_cycle()
        
        g.add_edge("c", "a")
        assert g.has_cycle()
    
    def test_has_cycle_undirected(self):
        """Test cycle detection in undirected graph."""
        g = Graph(directed=False)
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        
        assert not g.has_cycle()
        
        g.add_edge("c", "a")
        assert g.has_cycle()
    
    def test_get_degree(self):
        """Test getting node degree."""
        g = Graph(directed=True)
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        g.add_edge("d", "a")
        
        in_deg, out_deg = g.get_degree("a")
        
        assert in_deg == 1
        assert out_deg == 2
    
    def test_serialization(self):
        """Test graph serialization and deserialization."""
        g = Graph()
        g.add_node("n1", label="Node 1", node_type="domain")
        g.add_edge("n1", "n2", weight=0.5, relation="resolves_to")
        
        # Serialize
        data = g.to_dict()
        json_str = g.to_json()
        
        # Deserialize
        g2 = Graph.from_dict(data)
        g3 = Graph.from_json(json_str)
        
        assert len(g2) == 2
        assert len(g3) == 2
        assert g2.has_edge("n1", "n2")
    
    def test_stats(self):
        """Test graph statistics."""
        g = Graph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        
        stats = g.stats()
        
        assert stats["nodes"] == 3
        assert stats["edges"] == 2
        assert stats["directed"] == True


class TestGraphNode:
    """Test suite for GraphNode."""
    
    def test_create_node(self):
        """Test creating a node."""
        node = GraphNode(id="n1", label="Node 1", node_type="domain")
        
        assert node.id == "n1"
        assert node.label == "Node 1"
        assert node.node_type == "domain"
        assert len(node.edges) == 0
    
    def test_add_edge_to_node(self):
        """Test adding edge from node."""
        node = GraphNode(id="n1", label="Node 1", node_type="domain")
        edge = node.add_edge("n2", weight=0.5, relation="resolves_to")
        
        assert len(node.edges) == 1
        assert edge.target == "n2"
        assert edge.weight == 0.5
    
    def test_remove_edge_from_node(self):
        """Test removing edge from node."""
        node = GraphNode(id="n1", label="Node 1", node_type="domain")
        node.add_edge("n2")
        
        assert node.remove_edge("n2")
        assert len(node.edges) == 0
    
    def test_get_neighbors(self):
        """Test getting neighbors from node."""
        node = GraphNode(id="n1", label="Node 1", node_type="domain")
        node.add_edge("n2")
        node.add_edge("n3")
        
        neighbors = node.get_neighbors()
        assert neighbors == ["n2", "n3"]


