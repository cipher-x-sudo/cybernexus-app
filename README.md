# CyberNexus

<p align="center">
  <img src="docs/assets/logo.png" alt="CyberNexus Logo" width="200">
</p>

<h3 align="center">Enterprise Threat Intelligence Platform</h3>

<p align="center">
  <strong>The single pane of glass for organizational security intelligence</strong>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Node.js-18+-green.svg" alt="Node.js 18+">
  <img src="https://img.shields.io/badge/FastAPI-0.109.0-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js-14.0.4-black.svg" alt="Next.js 14">
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#capabilities">Capabilities</a> •
  <a href="#installation">Installation</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#documentation">Documentation</a>
</p>

---

## Introduction

**CyberNexus** is a next-generation, enterprise-grade Threat Intelligence and Exposure Management platform. Unlike fragmented point solutions, CyberNexus unifies reconnaissance, threat detection, credential monitoring, dark web surveillance, and security training into a single platform with a stunning professional interface.

Built with **custom Data Structure and Algorithm (DSA) implementations** at its core for high-performance in-memory operations, combined with **PostgreSQL** for persistent data storage and **Redis** for caching. This hybrid architecture delivers both algorithmic power and reliable persistence.

## Features

### Core Capabilities

- 🔍 **Exposure Discovery** - Automated external attack surface reconnaissance and asset discovery
- 🌐 **Dark Web Intelligence** - Monitor dark web for leaked credentials, brand mentions, and threats
- ✉️ **Email Security Assessment** - Test SPF, DKIM, DMARC configurations and detect spoofing vulnerabilities
- 🏗️ **Infrastructure Testing** - Scan for server misconfigurations, CVEs, and security vulnerabilities
- 🛡️ **Network Security Monitoring** - Detect HTTP tunneling, covert channels, and firewall bypass attempts
- 🔬 **Investigation Mode** - Deep analysis of suspicious URLs, domains, and artifacts with screenshot capture

### Advanced Features

- 🕸️ **Graph-Based Correlation** - Visualize threat relationships in 3D interactive graphs
- 🗺️ **Geographic Threat Maps** - See attacks and threats on an interactive world map
- ⚡ **Real-Time Alerts** - Instant notifications for critical threats via WebSocket
- 📊 **Custom Dashboards** - Drag-and-drop widget builder for personalized views
- 📄 **Professional Reports** - Executive-ready PDF/HTML exports with comprehensive findings
- 📅 **Scheduled Searches** - Automate recurring security scans with cron-based scheduling
- 📈 **Risk Scoring Engine** - Calculate and track risk scores for assets over time
- 🔒 **Network Logging & Blocking** - Real-time network traffic analysis and threat blocking
- 🕳️ **Tunnel Detection** - Advanced detection of HTTP and DNS tunneling attempts
- 📱 **WebSocket Streaming** - Real-time findings streaming during job execution
- 🎯 **Priority-Based Job Queue** - Intelligent job scheduling with priority levels

## Capabilities

### Exposure Discovery
Discover what attackers can find about your organization online. Automated reconnaissance scans domains, subdomains, and exposed assets to identify potential attack vectors.

**Features:**
- Subdomain enumeration
- Exposed configuration detection
- Sensitive data discovery
- Asset mapping

### Dark Web Intelligence
Monitor dark web (.onion) sites for brand mentions, credential leaks, and threats targeting your organization.

**Features:**
- Dark web crawling and indexing
- Keyword monitoring
- Credential leak detection
- Marketplace scanning
- Real-time WebSocket updates

### Email Security Assessment
Test email authentication configuration and identify spoofing vulnerabilities.

**Features:**
- SPF, DKIM, DMARC validation
- Email bypass testing
- Infrastructure mapping
- Compliance scoring
- Historical comparison

### Infrastructure Testing
Scan servers and infrastructure for misconfigurations and vulnerabilities.

**Features:**
- Security header analysis
- Path traversal detection
- CRLF injection testing
- CVE scanning
- Information disclosure detection

### Network Security Monitoring
Detect tunneling attempts and covert channel vulnerabilities in network traffic.

**Features:**
- HTTP tunnel detection
- DNS tunnel detection
- Real-time traffic analysis
- Rate limiting and blocking
- Network log retention

### Investigation Mode
Deep analysis of suspicious URLs, domains, or artifacts with comprehensive capture.

**Features:**
- Screenshot capture
- HAR file generation
- Domain tree mapping
- Visual similarity comparison
- Resource mapping

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│   Dashboard │ 3D Graph │ Threat Map │ Timeline │ Reports        │
├─────────────────────────────────────────────────────────────────┤
│                     BACKEND (Python FastAPI)                    │
│         REST API + WebSocket + JWT Authentication               │
├─────────────────────────────────────────────────────────────────┤
│                    PERSISTENCE LAYER                            │
│  PostgreSQL (SQLAlchemy) │ Redis Cache │ Custom DSA (Memory)    │
├─────────────────────────────────────────────────────────────────┤
│                    CUSTOM DSA IN-MEMORY LAYER                   │
│     Graph │ AVL Tree │ HashMap │ Heap │ Trie │ Bloom Filter     │
├─────────────────────────────────────────────────────────────────┤
│                      COLLECTORS LAYER                           │
│  WebRecon │ DarkWatch │ ConfigAudit │ EmailAudit │ DomainTree   │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Overview

CyberNexus uses a **hybrid architecture** combining:

- **PostgreSQL**: Persistent storage for users, jobs, findings, and metadata
- **Redis**: Caching layer for performance optimization
- **Custom DSA**: In-memory data structures for high-performance operations (graph traversal, indexing, correlation)
- **FastAPI**: Async REST API with WebSocket support
- **Next.js**: Modern React frontend with server-side rendering

The custom DSA implementations handle real-time operations, while PostgreSQL ensures data durability and complex querying capabilities.

## Custom DSA Implementations

All data structures are implemented from scratch for optimal performance:

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
- PostgreSQL 15+ (or use Docker)
- Redis (optional, for caching)
- Docker & Docker Compose (optional, recommended)

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd cybernexus-app
```

2. **Set up Python environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables**
Create a `.env` file in the `backend` directory:
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cybernexus
SECRET_KEY=your-super-secret-key-change-in-production
TOR_PROXY_HOST=localhost
TOR_PROXY_PORT=9050
CORS_ORIGINS=http://localhost:3000
```

4. **Set up PostgreSQL**
```bash
# Using Docker
docker run -d \
  --name cybernexus-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cybernexus \
  -p 5432:5432 \
  postgres:15-alpine

# Or install PostgreSQL locally and create database
createdb cybernexus
```

5. **Run database migrations**
```bash
cd backend
alembic upgrade head
```

6. **Start the backend**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Configure environment**
Create a `.env.local` file:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

3. **Start development server**
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Docker Setup (Recommended)

1. **Start all services**
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Backend API server
- Frontend Next.js app
- Tor proxy (for dark web access)
- Redis (if configured)

2. **Check service status**
```bash
docker-compose ps
```

3. **View logs**
```bash
docker-compose logs -f backend
```

4. **Stop services**
```bash
docker-compose down
```

## Configuration

### Environment Variables

Key configuration options (see `backend/app/config.py` for full list):

#### Database
- `DATABASE_URL` - PostgreSQL connection string (required)
- `DATABASE_POOL_SIZE` - Connection pool size (default: 5)

#### Authentication
- `SECRET_KEY` - JWT secret key (required, change in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration (default: 30)

#### Tor/Dark Web
- `TOR_PROXY_HOST` - Tor proxy hostname (default: localhost)
- `TOR_PROXY_PORT` - Tor proxy port (default: 9050)
- `TOR_REQUIRED` - Require Tor for startup (default: false)
- `DARKWEB_BATCH_SIZE` - Batch size for dark web operations (default: 5)

#### Network Security
- `NETWORK_ENABLE_LOGGING` - Enable network traffic logging (default: true)
- `NETWORK_ENABLE_BLOCKING` - Enable threat blocking (default: true)
- `NETWORK_ENABLE_TUNNEL_DETECTION` - Enable tunnel detection (default: true)
- `NETWORK_RATE_LIMIT_IP` - Requests per minute per IP (default: 100)

#### CORS
- `CORS_ORIGINS` - Allowed origins (comma-separated or `*` for all)
- `CORS_DEBUG` - Enable CORS debugging (default: false)

#### Application
- `ENVIRONMENT` - Environment (development/production)
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)
- `DEBUG` - Enable debug mode (default: false)

## Project Structure

```
cybernexus-app/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/                 # REST API endpoints
│   │   │   └── routes/          # Route handlers
│   │   ├── core/                # Core functionality
│   │   │   ├── dsa/             # Custom data structures
│   │   │   ├── database/        # Database models and storage
│   │   │   └── engine/          # Correlation, prediction, ranking
│   │   ├── collectors/          # Data collection modules
│   │   │   └── darkwatch_modules/  # Dark web crawlers/extractors
│   │   ├── services/            # Business logic services
│   │   ├── middleware/          # Request middleware
│   │   ├── utils/               # Utility functions
│   │   ├── config.py            # Configuration settings
│   │   └── main.py              # FastAPI application
│   ├── migrations/              # Alembic database migrations
│   ├── tests/                   # Test suite
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile               # Backend Docker image
├── frontend/                     # Next.js frontend
│   ├── src/
│   │   ├── app/                 # Next.js app router pages
│   │   ├── components/          # React components
│   │   ├── contexts/            # React contexts
│   │   └── lib/                 # Utilities and API clients
│   ├── public/                  # Static assets
│   ├── package.json             # Node dependencies
│   └── Dockerfile               # Frontend Docker image
├── data/                         # Runtime data (generated)
│   ├── blobs/                    # Binary data storage
│   ├── cache/                    # Cache files
│   ├── events/                   # Event logs
│   ├── graph/                    # Graph data
│   ├── indices/                  # Search indices
│   └── reports/                  # Generated reports
├── docker-compose.yml            # Docker Compose configuration
└── README.md                     # This file
```

## Tech Stack

### Backend
- **Python 3.11+** - Programming language
- **FastAPI 0.109.0** - Modern async web framework
- **SQLAlchemy 2.0** - ORM with async support
- **Alembic** - Database migrations
- **PostgreSQL** - Primary database
- **Redis** - Caching layer
- **WebSockets** - Real-time communication
- **JWT** - Authentication
- **APScheduler** - Job scheduling
- **Playwright** - Browser automation
- **Pydantic** - Data validation
- **Loguru** - Logging

### Frontend
- **Next.js 14** - React framework with SSR
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **React Three Fiber** - 3D graphics
- **Three.js** - 3D library
- **Mapbox GL** - Maps
- **D3.js** - Data visualization
- **Recharts** - Charts
- **Socket.io** - WebSocket client
- **Zustand** - State management

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Tor** - Dark web access
- **Nginx** - Reverse proxy (optional)

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html
```

### Code Formatting

```bash
# Backend
cd backend
black .
isort .

# Frontend
cd frontend
npm run lint
```

### Database Migrations

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

### Docker Compose Deployment

The included `docker-compose.yml` provides a complete production-ready setup:

```bash
# Start all services
docker-compose up -d

# Scale services
docker-compose up -d --scale worker=3

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Considerations

1. **Environment Variables**: Set all required environment variables
2. **Database**: Use managed PostgreSQL service or configure backups
3. **Secrets**: Use secret management for `SECRET_KEY` and database credentials
4. **SSL/TLS**: Configure reverse proxy (Nginx/Traefik) with SSL certificates
5. **Monitoring**: Set up logging and monitoring (Prometheus, Grafana)
6. **Backups**: Configure regular database backups
7. **Scaling**: Use multiple worker instances for job processing

### Railway Deployment

The project includes Railway configuration files:
- `railway.json` - Railway service configuration
- `railway.toml` - Railway deployment settings
- `nixpacks.toml` - Build configuration

## API Documentation

Interactive API documentation is automatically generated by FastAPI:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

All endpoints are documented with request/response schemas, examples, and authentication requirements.

## Documentation

> **Note**: Comprehensive documentation is in development. The following resources are planned:

- **Quick Start Guide** - Get running in 5 minutes
- **User Guide** - Complete guide: what, why, who, and how
- **Architecture Guide** - Technical architecture details
- **DSA Documentation** - Custom data structure implementations
- **API Reference** - Complete REST API endpoint documentation

For now, refer to:
- API documentation at `/docs` endpoint
- Code comments and docstrings
- This README

## Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** following the code style
4. **Add tests** for new functionality
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write tests for new features
- Update documentation as needed
- Follow conventional commit messages

## Troubleshooting

### Common Issues

**Database Connection Errors**
- Ensure PostgreSQL is running
- Check `DATABASE_URL` environment variable
- Verify database exists: `psql -l | grep cybernexus`

**Tor Proxy Issues**
- Verify Tor is running: `curl --socks5 localhost:9050 https://check.torproject.org/api/ip`
- Check `TOR_PROXY_HOST` and `TOR_PROXY_PORT` settings
- Set `TOR_REQUIRED=false` if Tor is optional

**Port Already in Use**
- Change ports in configuration or stop conflicting services
- Backend default: 8000
- Frontend default: 3000
- PostgreSQL default: 5432

**Migration Errors**
- Ensure database is up to date: `alembic upgrade head`
- Check migration files in `backend/migrations/versions/`

**CORS Errors**
- Configure `CORS_ORIGINS` with your frontend URL
- Enable `CORS_DEBUG` for detailed logging

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ for the security community
</p>
