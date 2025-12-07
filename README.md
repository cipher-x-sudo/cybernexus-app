# CyberNexus

<p align="center">
  <img src="docs/assets/logo.png" alt="CyberNexus Logo" width="200">
</p>

<h3 align="center">Enterprise Threat Intelligence Platform</h3>

<p align="center">
  <strong>The single pane of glass for organizational security intelligence</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#dsa">Custom DSA</a> •
  <a href="#documentation">Docs</a>
</p>

---

## Introduction

**CyberNexus** is a next-generation, enterprise-grade Threat Intelligence and Exposure Management platform. Unlike fragmented point solutions, CyberNexus unifies reconnaissance, threat detection, credential monitoring, dark web surveillance, and security training into a single platform with a stunning professional interface.

Built with **custom Data Structure and Algorithm (DSA) implementations** at its core - no external databases, just pure algorithmic power.

## Features

- 🔍 **Asset Discovery** - Automated external attack surface reconnaissance
- 🌐 **Dark Web Monitoring** - Track leaked credentials and brand abuse
- 🕸️ **Graph-Based Correlation** - Visualize threat relationships in 3D
- 🗺️ **Geographic Threat Maps** - See attacks on an interactive world map
- ⚡ **Real-Time Alerts** - Instant notifications for critical threats
- 📊 **Custom Dashboards** - Drag-and-drop widget builder
- 📄 **Professional Reports** - Executive-ready PDF/HTML exports
- 🎓 **Training Labs** - Auto-generated social engineering scenarios

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│   Dashboard │ 3D Graph │ Threat Map │ Timeline │ Reports        │
├─────────────────────────────────────────────────────────────────┤
│                     BACKEND (Python FastAPI)                     │
│         REST API + WebSocket + JWT Authentication               │
├─────────────────────────────────────────────────────────────────┤
│                    CUSTOM DSA DATABASE LAYER                     │
│     Graph │ AVL Tree │ HashMap │ Heap │ Trie │ Bloom Filter     │
├─────────────────────────────────────────────────────────────────┤
│                      COLLECTORS LAYER                            │
│  WebRecon │ DarkWatch │ ConfigAudit │ EmailAudit │ Credentials  │
└─────────────────────────────────────────────────────────────────┘
```

## Custom DSA Implementations

All data structures are implemented from scratch:

| Structure | Use Case |
|-----------|----------|
| **Graph** | Entity relationships, threat mapping |
| **AVL Tree** | IOC indexing, fast lookups |
| **HashMap** | O(1) correlation lookups |
| **Heap** | Priority-based threat ranking |
| **Trie** | Domain/keyword pattern matching |
| **Bloom Filter** | Fast deduplication |
| **B-Tree** | Disk-based persistence |
| **Linked List** | Timeline traversal |
| **Circular Buffer** | Event streaming |
| **Skip List** | Range queries |

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up -d
```

## Project Structure

```
cybernexus/
├── backend/          # Python FastAPI backend
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── core/     # DSA + Database + Engine
│   │   ├── collectors/  # Data ingestion modules
│   │   └── services/ # Business logic
│   └── tests/
├── frontend/         # Next.js frontend
│   └── src/
│       ├── app/      # Pages
│       └── components/
└── docs/             # Documentation
```

## Documentation

- **🚀 [Quick Start](docs/QUICKSTART.md)** - Get running in 5 minutes
- **📘 [Complete User Guide](docs/GUIDE.md)** - Comprehensive guide: what, why, who, and how
- [Architecture Guide](docs/ARCHITECTURE.md) - Technical architecture details
- [DSA Documentation](docs/DSA.md) - Custom data structure implementations
- [API Reference](docs/API.md) - REST API endpoints

### Quick Links

| I want to... | Go to... |
|--------------|----------|
| Understand what CyberNexus is | [User Guide - Overview](docs/GUIDE.md#what-is-cybernexus) |
| See who should use it | [User Guide - Users](docs/GUIDE.md#who-should-use-cybernexus) |
| Learn how it works | [User Guide - How It Works](docs/GUIDE.md#how-it-works) |
| Get started quickly | [User Guide - Getting Started](docs/GUIDE.md#getting-started) |
| Explore DSA implementations | [DSA Documentation](docs/DSA.md) |
| Integrate with the API | [API Reference](docs/API.md) |

## Tech Stack

**Backend:** Python 3.11, FastAPI, WebSockets, JWT

**Frontend:** Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Three.js, Mapbox GL

**Visualization:** React Three Fiber, D3.js, Recharts

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ for the security community
</p>


