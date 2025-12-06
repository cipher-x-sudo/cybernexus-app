# Custom DSA Implementations

## Overview

CyberNexus uses **100% custom Data Structure and Algorithm implementations** - no external database dependencies. This provides:

1. **Educational Value**: Clear demonstration of DSA concepts
2. **Performance Control**: Optimized for security use cases
3. **Independence**: No external database setup required
4. **Flexibility**: Custom operations for threat intelligence

## Data Structures

### 1. Graph (Adjacency List)

**Location:** `backend/app/core/dsa/graph.py`

**Features:**
- Directed and undirected support
- Weighted edges with relationship types
- BFS and DFS traversals
- Dijkstra's shortest path
- Connected components detection
- Cycle detection

**Use Cases:**
- Entity relationship mapping
- Attack path visualization
- Threat actor infrastructure correlation

**Complexity:**
- Add node: O(1)
- Add edge: O(1)
- BFS/DFS: O(V + E)
- Dijkstra: O((V + E) log V)

### 2. AVL Tree (Self-Balancing BST)

**Location:** `backend/app/core/dsa/avl_tree.py`

**Features:**
- Automatic balancing on insert/delete
- Range queries
- Floor and ceiling operations
- In-order, pre-order, post-order traversals

**Use Cases:**
- IOC (Indicators of Compromise) indexing
- Fast entity lookups
- Timestamp-based range queries

**Complexity:**
- Insert: O(log n)
- Search: O(log n)
- Delete: O(log n)
- Range query: O(log n + k)

### 3. HashMap (Separate Chaining)

**Location:** `backend/app/core/dsa/hashmap.py`

**Features:**
- Automatic resizing
- Collision handling with chaining
- Load factor monitoring

**Use Cases:**
- O(1) entity correlation
- DNS record caching
- Configuration lookups

**Complexity:**
- Insert: O(1) average
- Search: O(1) average
- Delete: O(1) average

### 4. Heap (Binary Min/Max)

**Location:** `backend/app/core/dsa/heap.py`

**Features:**
- Min-heap and max-heap variants
- Priority queue operations
- Efficient top-N retrieval

**Use Cases:**
- Threat severity ranking
- Alert priority queue
- Task scheduling

**Complexity:**
- Insert: O(log n)
- Extract: O(log n)
- Peek: O(1)
- Heapify: O(n)

### 5. Trie (Prefix Tree)

**Location:** `backend/app/core/dsa/trie.py`

**Features:**
- Prefix matching
- Autocomplete suggestions
- Pattern matching with wildcards
- Word count statistics

**Use Cases:**
- Domain name matching
- Keyword pattern search
- Dork query storage

**Complexity:**
- Insert: O(m) where m = key length
- Search: O(m)
- Prefix match: O(m + k) where k = results

### 6. Bloom Filter

**Location:** `backend/app/core/dsa/bloom_filter.py`

**Features:**
- Probabilistic membership testing
- Configurable false positive rate
- Memory efficient
- Counting variant for deletions

**Use Cases:**
- URL deduplication during crawling
- Quick "have we seen this?" checks
- Reducing expensive lookups

**Complexity:**
- Insert: O(k) where k = hash functions
- Query: O(k)
- Space: O(m) bits

### 7. B-Tree

**Location:** `backend/app/core/dsa/btree.py`

**Features:**
- Disk-optimized structure
- Configurable branching factor
- Range queries
- All leaves at same level

**Use Cases:**
- Persistent index storage
- Large dataset indexing
- Efficient range queries on disk

**Complexity:**
- Insert: O(log n)
- Search: O(log n)
- Delete: O(log n)

### 8. Skip List

**Location:** `backend/app/core/dsa/skip_list.py`

**Features:**
- Probabilistic balancing
- Range queries
- Floor and ceiling operations
- Simple implementation

**Use Cases:**
- Timestamp-based queries
- Alternative to balanced trees
- Ordered event storage

**Complexity:**
- Insert: O(log n) expected
- Search: O(log n) expected
- Delete: O(log n) expected

### 9. Doubly Linked List

**Location:** `backend/app/core/dsa/linked_list.py`

**Features:**
- Bidirectional traversal
- O(1) insertion/deletion at ends
- Iterator support

**Use Cases:**
- Timeline event storage
- Event history traversal
- LRU cache implementation

**Complexity:**
- Insert at head/tail: O(1)
- Delete at head/tail: O(1)
- Search: O(n)

### 10. Circular Buffer

**Location:** `backend/app/core/dsa/circular_buffer.py`

**Features:**
- Fixed-size buffer
- Automatic overwrite of oldest items
- Time-windowed variant

**Use Cases:**
- Rolling event logs
- Real-time traffic analysis
- Recent activity tracking

**Complexity:**
- Push: O(1)
- Pop: O(1)
- Access: O(1)

## Integration Examples

### Threat Correlation

```python
from app.core.dsa import Graph, AVLTree, HashMap

# Create graph for entity relationships
graph = Graph(directed=True)
graph.add_node("domain.com", node_type="domain")
graph.add_node("192.168.1.1", node_type="ip")
graph.add_edge("domain.com", "192.168.1.1", relation="resolves_to")

# Index entities for fast lookup
index = AVLTree()
index.insert(timestamp, entity_id)

# Cache DNS lookups
cache = HashMap()
cache.put("domain.com", dns_record)
```

### Threat Ranking

```python
from app.core.dsa import MaxHeap

# Priority-based threat ranking
ranker = MaxHeap()
ranker.push(severity_score, threat_id)

# Get top 10 threats
top_threats = ranker.get_top_n(10)
```

### URL Deduplication

```python
from app.core.dsa import BloomFilter

# Fast URL deduplication
seen = BloomFilter(expected_items=1000000, false_positive_rate=0.01)

if not seen.contains(url):
    seen.add(url)
    process_url(url)
```


