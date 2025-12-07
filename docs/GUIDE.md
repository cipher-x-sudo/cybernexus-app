# CyberNexus - Complete User Guide

<p align="center">
  <img src="assets/logo.png" alt="CyberNexus Logo" width="180">
</p>

<h2 align="center">Enterprise Threat Intelligence Platform</h2>

<p align="center">
  <em>The single pane of glass for organizational security intelligence</em>
</p>

---

## Table of Contents

1. [What is CyberNexus?](#what-is-cybernexus)
2. [Why Use CyberNexus?](#why-use-cybernexus)
3. [Who Should Use CyberNexus?](#who-should-use-cybernexus)
4. [Key Features](#key-features)
5. [How It Works](#how-it-works)
6. [Getting Started](#getting-started)
7. [Using the Platform](#using-the-platform)
8. [Use Cases & Scenarios](#use-cases--scenarios)
9. [Technical Deep Dive](#technical-deep-dive)
10. [FAQ](#faq)

---

## What is CyberNexus?

**CyberNexus** is a next-generation, enterprise-grade **Threat Intelligence and Exposure Management** platform. It unifies multiple critical security functions into a single, cohesive system:

- 🔍 **Reconnaissance** - Automated discovery of your external attack surface
- 🕵️ **Threat Detection** - Real-time identification of security threats
- 🔐 **Credential Monitoring** - Track leaked passwords and compromised accounts
- 🌑 **Dark Web Surveillance** - Monitor underground forums and marketplaces
- 📊 **Security Analytics** - Visualize and analyze threat relationships

### What Makes CyberNexus Unique?

Unlike traditional security tools that rely on external databases (PostgreSQL, MongoDB, Redis), CyberNexus is built on **100% custom Data Structure and Algorithm (DSA) implementations**. This means:

- **Zero Database Dependencies** - No external database setup required
- **Educational Value** - Clear demonstration of computer science fundamentals
- **Optimized Performance** - Algorithms tailored for security intelligence operations
- **Complete Transparency** - Every line of code is auditable

---

## Why Use CyberNexus?

### The Problem

Modern organizations face fragmented security tooling:

| Challenge | Impact |
|-----------|--------|
| **Tool Sprawl** | Security teams juggle 10+ separate tools |
| **Alert Fatigue** | Thousands of disconnected alerts daily |
| **Blind Spots** | No unified view of the attack surface |
| **Slow Response** | Manual correlation delays threat response |
| **Hidden Threats** | Dark web exposure goes undetected |

### The Solution

CyberNexus provides a **unified security intelligence layer**:

```
Traditional Approach          CyberNexus Approach
───────────────────          ────────────────────
Tool A → Alert              ┌─────────────────────┐
Tool B → Alert     vs       │                     │
Tool C → Alert              │  Single Dashboard   │
Tool D → Alert              │  Correlated Intel   │
Tool E → Alert              │  Prioritized Threats│
(Manual correlation)        │                     │
                            └─────────────────────┘
```

### Key Benefits

| Benefit | Description |
|---------|-------------|
| **🎯 Unified View** | All security intelligence in one dashboard |
| **⚡ Real-Time Alerts** | Instant notifications for critical threats |
| **🔗 Automatic Correlation** | Graph-based relationship discovery |
| **📈 Priority Ranking** | Focus on what matters most |
| **📄 Executive Reports** | Professional PDF/HTML exports |
| **🎓 Educational** | Learn DSA through practical application |

---

## Who Should Use CyberNexus?

### Primary Users

#### 1. 🛡️ Security Operations Center (SOC) Teams
- **Use Case**: Real-time threat monitoring and incident response
- **Value**: Unified view of all security events, faster triage

#### 2. 👨‍💻 Penetration Testers & Red Teams
- **Use Case**: External reconnaissance and attack surface mapping
- **Value**: Automated asset discovery, dork generation

#### 3. 🔐 Cybersecurity Analysts
- **Use Case**: Threat intelligence analysis and correlation
- **Value**: Graph-based visualization of threat relationships

#### 4. 📊 Security Managers & CISOs
- **Use Case**: Executive reporting and risk assessment
- **Value**: Professional reports, security scoring

#### 5. 🎓 Students & Educators
- **Use Case**: Learning data structures and algorithms
- **Value**: Real-world application of CS fundamentals

### Organization Types

| Organization | Use Case |
|--------------|----------|
| **Enterprises** | Comprehensive attack surface management |
| **Financial Services** | Fraud detection, credential monitoring |
| **Healthcare** | Patient data protection, compliance |
| **Government** | National security, infrastructure protection |
| **Academia** | Research, education, DSA learning |
| **Startups** | Cost-effective security intelligence |

---

## Key Features

### 🔍 Asset Discovery

Automatically discover your external attack surface through:

- **Subdomain Enumeration** - Find all subdomains of your domains
- **Google Dorking** - Generate advanced search queries
- **Endpoint Discovery** - Identify exposed APIs, admin panels
- **Technology Detection** - Map your tech stack

```
┌─────────────────────────────────────────────────┐
│  Asset Discovery Results                        │
├─────────────────────────────────────────────────┤
│  Domain: example.com                            │
│  ─────────────────────────────────────────────  │
│  📁 Subdomains Found: 47                        │
│     - api.example.com (HTTP 200)                │
│     - staging.example.com (HTTP 403)            │
│     - admin.example.com (HTTP 302)              │
│                                                 │
│  🔗 Endpoints Discovered: 23                    │
│     - /api/v1 (Swagger UI)                      │
│     - /.git/config (EXPOSED!)                   │
│     - /robots.txt (OK)                          │
│                                                 │
│  🔧 Technologies: React, Node.js, AWS           │
└─────────────────────────────────────────────────┘
```

### 🌐 Dark Web Monitoring

Track your organization's exposure on the dark web:

- **Brand Monitoring** - Detect mentions of your company
- **Credential Leaks** - Find exposed passwords
- **Data Breaches** - Monitor for leaked data
- **Threat Actor Tracking** - Follow malicious actors

**Categories Monitored:**
- Ransomware leak sites
- Underground marketplaces
- Hacking forums
- Credential dump sites
- Carding platforms

### 🕸️ Graph-Based Correlation

Visualize threat relationships in interactive 3D:

```
                    ┌─────────┐
                    │ Domain  │
                    │example  │
                    │ .com    │
                    └────┬────┘
                         │resolves_to
              ┌──────────┴──────────┐
              ▼                     ▼
        ┌─────────┐           ┌─────────┐
        │   IP    │           │   IP    │
        │1.2.3.4  │           │5.6.7.8  │
        └────┬────┘           └────┬────┘
             │hosts                │hosts
             ▼                     ▼
        ┌─────────┐           ┌─────────┐
        │ Service │           │ Service │
        │ Apache  │           │  Nginx  │
        └─────────┘           └─────────┘
```

**Graph Features:**
- 3D interactive visualization with Three.js
- Node filtering by type (domain, IP, email, etc.)
- Path finding between entities
- Cluster detection
- Export capabilities

### 🗺️ Geographic Threat Maps

See attacks on an interactive world map:

- Real-time attack visualization
- Country-based threat statistics
- IP geolocation
- Attack origin tracking

### ⚡ Real-Time Alerts

Instant notifications for critical events:

| Alert Type | Trigger |
|------------|---------|
| **Critical Threat** | High-severity vulnerability discovered |
| **Credential Leak** | Company credentials found on dark web |
| **Brand Mention** | Organization mentioned on threat forums |
| **New Exposure** | New asset exposed to internet |
| **Configuration Issue** | Security misconfiguration detected |

### 📊 Custom Dashboards

Build personalized views:

- Drag-and-drop widget placement
- Multiple dashboard layouts
- Real-time data updates
- Dark theme optimized

### 📄 Professional Reports

Generate executive-ready documentation:

- **Executive Summary** - High-level overview for leadership
- **Technical Report** - Detailed findings for security teams
- **Compliance Report** - Audit-ready documentation
- **Trend Analysis** - Historical security posture

**Export Formats:** PDF, HTML, JSON

---

## How It Works

### Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                    EXPERIENCE LAYER (Frontend)                      │
│   Next.js 14 │ React │ TypeScript │ Tailwind │ Three.js            │
│   ─────────────────────────────────────────────────────────────    │
│   Dashboard  │  3D Graph  │  Threat Map  │  Timeline  │  Reports   │
├────────────────────────────────────────────────────────────────────┤
│                        API LAYER (Backend)                          │
│           FastAPI │ WebSockets │ JWT Auth │ REST API               │
│   ─────────────────────────────────────────────────────────────    │
│   /entities  │  /graph  │  /threats  │  /timeline  │  /reports     │
├────────────────────────────────────────────────────────────────────┤
│                     ANALYSIS ENGINE LAYER                           │
│        Correlator  │  Ranker  │  Predictor  │  Pattern Detection   │
├────────────────────────────────────────────────────────────────────┤
│                   CUSTOM DSA DATABASE LAYER                         │
│   Graph │ AVL Tree │ HashMap │ Heap │ Trie │ Bloom Filter │ B-Tree │
├────────────────────────────────────────────────────────────────────┤
│                       COLLECTORS LAYER                              │
│   WebRecon │ DarkWatch │ ConfigAudit │ EmailAudit │ Credentials    │
└────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. COLLECTION           2. STORAGE              3. ANALYSIS
   ───────────            ────────              ──────────
   Collectors   ───▶   DSA Structures   ───▶   Correlator
   (WebRecon,          (Graph, Heap,           (Pattern
   DarkWatch,           Trie, etc.)            Detection)
   etc.)
        │                    │                      │
        │                    │                      │
        ▼                    ▼                      ▼
4. PRESENTATION         5. ACTION              6. FEEDBACK
   ──────────────         ───────               ─────────
   Dashboard,          User Response,         Updated
   Alerts,             Remediation,           Priorities
   Reports             Investigation
```

### Custom Data Structures

CyberNexus uses **10 custom DSA implementations**:

| Structure | Purpose | Complexity |
|-----------|---------|------------|
| **Graph** | Entity relationships, threat mapping | O(V+E) traversal |
| **AVL Tree** | IOC indexing, fast lookups | O(log n) operations |
| **HashMap** | O(1) correlation lookups | O(1) average |
| **Heap** | Priority-based threat ranking | O(log n) operations |
| **Trie** | Domain/keyword pattern matching | O(m) where m=length |
| **Bloom Filter** | Fast URL deduplication | O(k) operations |
| **B-Tree** | Disk-based persistence | O(log n) operations |
| **Linked List** | Timeline traversal | O(1) insert/delete |
| **Circular Buffer** | Event streaming | O(1) operations |
| **Skip List** | Range queries | O(log n) expected |

### Collectors

Data collection modules inspired by industry tools:

| Collector | Inspired By | Purpose |
|-----------|-------------|---------|
| **WebRecon** | oxdork | Asset discovery, dorking |
| **DomainTree** | lookyloo | Domain analysis tree |
| **ConfigAudit** | nginxpwner | Configuration scanning |
| **EmailAudit** | espoofer | Email security analysis |
| **DarkWatch** | freshonions | Dark web monitoring |
| **KeywordMonitor** | VigilantOnion | Keyword alerting |
| **CredentialAnalyzer** | RDPassSpray | Credential intelligence |
| **TunnelDetector** | Tunna | Tunnel detection |
| **TrainingKB** | awesome-social-engineering | SE knowledge base |

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker** (optional)

### Installation Options

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/cybernexus.git
cd cybernexus

# Start with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### Option 2: Manual Setup

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Default Credentials

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Administrator |
| `analyst` | `analyst123` | Security Analyst |

> ⚠️ **Important**: Change default credentials immediately in production!

### First Steps

1. **Login** to the dashboard
2. **Add your organization's domains** to monitor
3. **Configure alert thresholds**
4. **Set up dark web keywords** (company name, domains, executive names)
5. **Run initial reconnaissance scan**

---

## Using the Platform

### Dashboard

The main dashboard provides an at-a-glance view of your security posture:

| Widget | Description |
|--------|-------------|
| **Global Threat Map** | Real-time visualization of attacks worldwide |
| **Threat Statistics** | Total threats, critical, resolved |
| **Security Score** | Overall security health (0-100) |
| **Activity Feed** | Recent security events |
| **Charts** | Threat trends, category distribution |

### 3D Threat Graph

Navigate the interactive entity graph:

| Control | Action |
|---------|--------|
| **Click + Drag** | Rotate view |
| **Scroll** | Zoom in/out |
| **Click Node** | View entity details |
| **Right-click** | Context menu (expand, isolate, etc.) |
| **Double-click** | Focus on node |

**Node Types & Colors:**
- 🔵 **Blue** - Domains
- 🟢 **Green** - IP Addresses
- 🟡 **Yellow** - Emails
- 🔴 **Red** - Threats
- 🟣 **Purple** - Services

### Dark Web Monitoring

The DarkWatch module tracks:

1. **Brand Mentions** - When your company is mentioned
2. **Credential Leaks** - Exposed usernames/passwords
3. **Data Breaches** - Leaked databases
4. **Ransomware Sites** - Victim lists

**Alert Priority:**
- 🔴 **Critical** - Confirmed credential exposure
- 🟠 **High** - Data breach mention
- 🟡 **Medium** - Brand discussion
- 🔵 **Low** - Passive mention

### Generating Reports

1. Navigate to **Reports** section
2. Select report template:
   - Executive Summary
   - Technical Assessment
   - Compliance Report
3. Choose date range
4. Select format (PDF/HTML)
5. Click **Generate**

---

## Use Cases & Scenarios

### Scenario 1: Credential Breach Response

**Situation:** Your organization's credentials appear in a dark web dump.

**CyberNexus Response:**

```
1. DarkWatch detects credentials matching your domain
2. Critical alert triggered instantly
3. Graph shows affected users and related entities
4. Timeline shows when credentials were first seen
5. Report generated for incident response team
```

**Actions Enabled:**
- Immediate password reset for affected accounts
- Correlation with previous phishing attempts
- Executive notification with impact assessment

### Scenario 2: External Attack Surface Discovery

**Situation:** You need to map your organization's external exposure.

**CyberNexus Response:**

```
1. WebRecon scans primary domains
2. Subdomains enumerated automatically
3. Exposed endpoints identified (.git, .env, etc.)
4. Technologies fingerprinted
5. Risk-scored findings prioritized
```

**Discoveries May Include:**
- Forgotten staging environments
- Exposed admin panels
- Sensitive file exposure
- Shadow IT assets

### Scenario 3: Threat Actor Investigation

**Situation:** You're tracking a specific threat actor targeting your industry.

**CyberNexus Response:**

```
1. Set keywords: actor name, TTPs, IOCs
2. DarkWatch monitors dark web forums
3. Graph builds relationship map:
   Actor → Infrastructure → Targets → Techniques
4. Timeline shows activity patterns
5. Predictive analysis suggests next moves
```

### Scenario 4: Security Posture Reporting

**Situation:** Board meeting requires security status update.

**CyberNexus Response:**

```
1. Navigate to Reports
2. Select "Executive Summary"
3. Choose last quarter date range
4. Generate PDF
5. Includes:
   - Security score trend
   - Threat statistics
   - Remediation progress
   - Industry benchmarking
```

---

## Technical Deep Dive

### Graph Implementation

The core Graph structure powers entity relationships:

```python
# Example: Adding threat relationships
from app.core.dsa import Graph

# Create directed graph
graph = Graph(directed=True)

# Add entities
graph.add_node("example.com", node_type="domain")
graph.add_node("192.168.1.1", node_type="ip")
graph.add_node("admin@example.com", node_type="email")

# Add relationships
graph.add_edge("example.com", "192.168.1.1", 
               relation="resolves_to", weight=1.0)
graph.add_edge("example.com", "admin@example.com",
               relation="whois_contact")

# Find paths
path = graph.shortest_path_bfs("example.com", "192.168.1.1")

# Get neighbors
neighbors = graph.get_neighbors("example.com", depth=2)

# Detect clusters
components = graph.connected_components()
```

### Bloom Filter for Deduplication

Efficient URL deduplication during crawling:

```python
from app.core.dsa import BloomFilter

# Create filter (10M capacity, 0.1% false positive)
seen_urls = BloomFilter(capacity=10_000_000, error_rate=0.001)

# Fast membership testing
if not seen_urls.contains(url):
    seen_urls.add(url)
    process_url(url)  # Only process new URLs
```

### Heap for Threat Prioritization

Priority-based threat ranking:

```python
from app.core.dsa import MaxHeap

# Create priority queue
ranker = MaxHeap()

# Add threats with severity scores
ranker.push(95, threat_1)  # Critical
ranker.push(72, threat_2)  # High
ranker.push(45, threat_3)  # Medium

# Get top 10 threats
top_threats = ranker.get_top_n(10)
```

### Trie for Pattern Matching

Efficient keyword and domain matching:

```python
from app.core.dsa import Trie

# Build keyword trie
keyword_trie = Trie()
keyword_trie.insert("ransomware")
keyword_trie.insert("credential")
keyword_trie.insert("breach")

# Fast prefix matching
matches = keyword_trie.search_prefix("rans")  # ["ransomware"]

# Autocomplete
suggestions = keyword_trie.autocomplete("cred")  # ["credential"]
```

### API Examples

**Authentication:**

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=admin123"

# Response
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Fetch Threats:**

```bash
# Get critical threats
curl http://localhost:8000/api/v1/threats?severity=critical \
  -H "Authorization: Bearer eyJ..."

# Response
{
  "threats": [
    {
      "id": "t-001",
      "title": "Exposed S3 Bucket",
      "severity": "critical",
      "score": 95
    }
  ]
}
```

**Graph Query:**

```bash
# Get entity graph
curl http://localhost:8000/api/v1/graph?limit=100 \
  -H "Authorization: Bearer eyJ..."

# Response
{
  "nodes": [...],
  "edges": [...]
}
```

---

## FAQ

### General Questions

**Q: Does CyberNexus require an external database?**

A: No! CyberNexus uses 100% custom DSA implementations. All data is stored using custom Graph, AVL Tree, HashMap, and other structures.

**Q: Is CyberNexus suitable for production use?**

A: CyberNexus is designed primarily as an educational project demonstrating DSA concepts in a real-world security context. For enterprise production use, additional hardening is recommended.

**Q: Can I extend CyberNexus with new collectors?**

A: Yes! The collector architecture is modular. Create a new collector in `backend/app/collectors/` following the existing patterns.

### Technical Questions

**Q: How does the Graph structure handle large datasets?**

A: The adjacency list implementation is memory-efficient with O(V+E) space complexity. For very large graphs, pagination and depth-limiting are recommended.

**Q: What's the false positive rate of the Bloom Filter?**

A: Configurable per use case. Default is 0.1% (1 in 1000) for URL deduplication.

**Q: How are threats prioritized?**

A: Multi-factor scoring using:
- Severity level (critical/high/medium/low)
- Entity relationships (graph centrality)
- Recency (newer = higher priority)
- Business context (configured keywords)

### Security Questions

**Q: How is authentication handled?**

A: JWT-based authentication with configurable expiration. Tokens are signed with HS256 algorithm.

**Q: Is data encrypted?**

A: Data at rest encryption is planned for future releases. Currently, file-based storage uses standard filesystem permissions.

**Q: What about dark web access?**

A: DarkWatch module is designed to interface with Tor. In the current version, it uses simulated data for demonstration. Production deployment would require Tor configuration.

---

## Support & Contributing

### Getting Help

- 📖 **Documentation**: This guide and `docs/` folder
- 🐛 **Issues**: GitHub Issues for bugs
- 💬 **Discussions**: GitHub Discussions for questions

### Contributing

We welcome contributions! Areas of interest:

1. **New Collectors** - Additional data sources
2. **DSA Improvements** - Performance optimizations
3. **UI Enhancements** - Dashboard widgets
4. **Documentation** - Tutorials and guides

### License

MIT License - See [LICENSE](../LICENSE) for details.

---

<p align="center">
  <strong>Built with ❤️ for the security community</strong>
</p>

<p align="center">
  <em>CyberNexus - Where Data Structures Meet Security Intelligence</em>
</p>

