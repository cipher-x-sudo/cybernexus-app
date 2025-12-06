# CyberNexus Architecture

## Overview

CyberNexus is built on a 4-layer architecture designed for scalability, performance, and extensibility.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXPERIENCE LAYER (Frontend)                   │
│   Next.js 14 │ React │ TypeScript │ Tailwind │ Three.js         │
├─────────────────────────────────────────────────────────────────┤
│                      API LAYER (Backend)                         │
│         FastAPI │ WebSockets │ JWT Auth │ REST API              │
├─────────────────────────────────────────────────────────────────┤
│                    ANALYSIS ENGINE LAYER                         │
│      Correlator │ Ranker │ Predictor │ Pattern Detection        │
├─────────────────────────────────────────────────────────────────┤
│                  CUSTOM DSA DATABASE LAYER                       │
│   Graph │ AVL Tree │ HashMap │ Heap │ Trie │ Bloom Filter       │
├─────────────────────────────────────────────────────────────────┤
│                     COLLECTORS LAYER                             │
│  WebRecon │ ConfigAudit │ EmailAudit │ DarkWatch │ Credentials  │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Details

### 1. Experience Layer (Frontend)

**Technology Stack:**
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS + shadcn/ui for styling
- Three.js / React Three Fiber for 3D visualization
- Mapbox GL for geographic visualization
- Recharts for data visualization
- Socket.io for real-time updates

**Key Components:**
- Dashboard with customizable widgets
- 3D Graph Explorer for entity relationships
- Geographic Threat Map
- Interactive Timeline
- Report Generator

### 2. API Layer (Backend)

**Technology Stack:**
- Python 3.11+
- FastAPI for REST API
- WebSockets for real-time communication
- JWT for authentication
- Pydantic for data validation

**Endpoints:**
- `/api/v1/auth` - Authentication
- `/api/v1/entities` - Entity CRUD
- `/api/v1/graph` - Graph queries
- `/api/v1/threats` - Threat management
- `/api/v1/timeline` - Event timeline
- `/api/v1/reports` - Report generation
- `/api/v1/ws` - WebSocket connections

### 3. Analysis Engine Layer

**Components:**

**Correlator:**
- Graph-based entity correlation
- Attack pattern identification
- Cluster detection
- Risk scoring

**Ranker:**
- Heap-based threat prioritization
- Multi-factor scoring
- Dynamic priority updates

**Predictor:**
- Password mutation prediction
- Typosquatting detection
- Threat evolution analysis

### 4. Custom DSA Database Layer

All data structures are implemented from scratch:

| Structure | Use Case | Complexity |
|-----------|----------|------------|
| Graph | Entity relationships | O(V+E) traversal |
| AVL Tree | IOC indexing | O(log n) operations |
| HashMap | Fast lookups | O(1) average |
| Min/Max Heap | Priority queues | O(log n) operations |
| Trie | Prefix matching | O(m) operations |
| Bloom Filter | Deduplication | O(k) operations |
| B-Tree | Disk persistence | O(log n) operations |
| Skip List | Range queries | O(log n) expected |
| Circular Buffer | Event streaming | O(1) operations |
| Linked List | Timeline traversal | O(1) insert/delete |

### 5. Collectors Layer

**Inspired By Reference Tools:**

| Collector | Inspired By | Purpose |
|-----------|-------------|---------|
| WebRecon | oxdork | Asset discovery, dorking |
| DomainTree | lookyloo | Domain analysis |
| ConfigAudit | nginxpwner | Misconfiguration scanning |
| EmailAudit | espoofer | Email security analysis |
| DarkWatch | freshonions | Dark web monitoring |
| KeywordMonitor | VigilantOnion | Keyword alerting |
| CredentialAnalyzer | RDPassSpray | Credential intelligence |
| TunnelDetector | Tunna | Tunnel detection |
| TrainingKB | awesome-social-engineering | SE knowledge base |

## Data Flow

```
Collectors → DSA Storage → Analysis Engine → API → Frontend
     ↑                                              ↓
     └──────────── User Actions ←───────────────────┘
```

1. **Collection**: Collectors gather data from various sources
2. **Storage**: Data stored using custom DSA structures
3. **Analysis**: Engine correlates and ranks threats
4. **Presentation**: Frontend displays insights
5. **Action**: Users respond to threats

## Security Considerations

- JWT-based authentication
- Role-based access control (planned)
- Data encryption at rest (planned)
- Audit logging
- Rate limiting
- Input validation with Pydantic


