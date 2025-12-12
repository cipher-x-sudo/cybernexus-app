# Dark Web Intelligence Features

## Overview

The Dark Web Intelligence capability in CyberNexus provides comprehensive monitoring and analysis of dark web (.onion) sites for threat intelligence, brand protection, and security monitoring.

---

## Core Features

### 1. **Multi-Engine URL Discovery** 🔍
**Parallel discovery from multiple sources:**
- **DarkWebEngine**: Discovers URLs from DiscoverDarkWeb service (`3bbaaaccczcbdddz.onion`)
- **SearchEngine**: Queries TORCH search engine (`xmh57jrzrnw6insl.onion`)
- **GistEngine**: Monitors GitHub Gists for .onion URLs
- **RedditEngine**: Scans Reddit posts for dark web mentions
- **PastebinEngine**: Monitors Pastebin for leaked data and URLs
- **SecurityNewsEngine**: Tracks security news sources

**Implementation**: All engines run in **parallel** using ThreadPoolExecutor for maximum speed.

---

### 2. **Site Crawling & Analysis** 🕷️
**Comprehensive site analysis:**
- Crawls .onion sites via Tor proxy (SOCKS5)
- Extracts page titles and content
- Detects site language automatically
- Tracks site online/offline status
- Follows linked .onion sites (configurable depth)
- **Parallel crawling** with configurable worker threads (default: 5)

---

### 3. **Entity Extraction** 🔎
**Automatically extracts sensitive data using regex patterns:**

| Entity Type | Pattern | Use Case |
|------------|---------|----------|
| **Emails** | `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z\|a-z]{2,}\b` | Leaked credentials |
| **Bitcoin Addresses** | Legacy & Bech32 formats | Cryptocurrency tracking |
| **Monero Addresses** | `\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b` | Privacy coin tracking |
| **Ethereum Addresses** | `\b0x[a-fA-F0-9]{40}\b` | Smart contract tracking |
| **SSH Fingerprints** | SHA256/MD5 formats | Server identification |
| **PGP Keys** | Public key blocks | Encryption keys |
| **Phone Numbers** | International format | Contact information |
| **IP Addresses** | IPv4 format | Network infrastructure |
| **Credit Cards** | Visa, Mastercard, Amex | Financial fraud detection |
| **Onion URLs** | v2 (16 chars) & v3 (56 chars) | Site relationships |

---

### 4. **Site Categorization** 📂
**Automatically categorizes sites into 15 categories:**

- **MARKETPLACE** - Dark web marketplaces
- **FORUM** - Discussion forums
- **LEAK_SITE** - Data breach/leak sites
- **RANSOMWARE** - Ransomware groups
- **CARDING** - Credit card fraud sites
- **DRUGS** - Drug marketplaces
- **HACKING** - Hacking tools/exploits
- **FRAUD** - Scam/counterfeit sites
- **CRYPTO** - Cryptocurrency services
- **WEAPONS** - Weapons marketplaces
- **COUNTERFEIT** - Fake documents/IDs
- **HOSTING** - Anonymous hosting
- **SEARCH** - Search engines
- **SOCIAL** - Social media platforms
- **NEWS** - News sites
- **UNKNOWN** - Uncategorized

**Method**: Keyword-based categorization with YARA rule support.

---

### 5. **Brand & Keyword Monitoring** 🎯
**Monitors for specific keywords/brands:**
- Real-time keyword matching using Trie data structure
- Context extraction around matches
- Brand mention tracking with timestamps
- Impersonation detection
- Data leak identification
- Threat level assignment per mention

**Features:**
- Add/remove monitored keywords dynamically
- Case-insensitive matching
- Context preservation (surrounding text)
- Multiple keyword support per job

---

### 6. **Risk Scoring & Threat Levels** ⚠️
**Intelligent risk assessment:**

**Risk Score Calculation:**
- **Category Weight** (0.3-0.9):
  - Ransomware: 0.9
  - Leak Site: 0.85
  - Carding: 0.8
  - Hacking: 0.75
  - Marketplace: 0.6
  - Forum: 0.4

- **Entity Weight** (per entity):
  - Credit Card: +0.3
  - Email: +0.1
  - SSH Fingerprint: +0.15
  - Bitcoin: +0.05

- **Keyword Matches**: +0.15 per matched keyword

**Threat Levels:**
- **CRITICAL** (≥0.8): Immediate action required
- **HIGH** (≥0.6): High priority investigation
- **MEDIUM** (≥0.4): Monitor closely
- **LOW** (≥0.2): Low priority
- **INFO** (<0.2): Informational only

---

### 7. **Site Relationship Mapping** 🕸️
**Graph-based relationship visualization:**
- Maps connections between .onion sites
- Tracks linked sites discovered during crawling
- BFS traversal for network analysis
- Visualizes site clusters and communities
- Identifies central nodes (high connectivity)

**Data Structure**: Custom Graph implementation with directed edges.

---

### 8. **Clone Detection** 🔄
**Identifies duplicate/cloned sites:**
- Content hash comparison (SHA256)
- Normalized content matching
- Detects site mirrors and copies
- Helps identify phishing/impersonation sites

---

### 9. **Language Detection** 🌍
**Automatic language identification:**
- Detects site language from content
- Supports multiple languages
- Fallback detection for short content
- Language-based filtering

---

### 10. **YARA Rule Matching** 🎯
**Pattern-based categorization and keyword detection:**
- **categories.yar**: Site categorization rules
- **keywords.yar**: Brand/keyword matching rules
- Score-based matching (metadata in rules)
- Extensible rule system

---

### 11. **URL Database Management** 💾
**Persistent storage:**
- SQLite database for URL tracking
- Tracks discovery source and date
- Status monitoring (Online/Offline/Unknown)
- Category and keyword scores
- Last scan timestamps
- Retry logic for offline sites

---

### 12. **Parallel Processing** ⚡
**High-performance execution:**
- **URL Discovery**: All engines run in parallel
- **Site Crawling**: Configurable worker threads (default: 5)
- **Thread-safe findings storage** with locks
- **Progress tracking** for parallel operations
- **Timeout handling** per operation

**Performance:**
- URL Discovery: ~5-6x faster (parallel engines)
- Site Crawling: ~3-5x faster (parallel workers)
- Total time: Reduced from 5-10 minutes to 1-3 minutes

---

### 13. **Incremental Polling** 📡
**Real-time findings retrieval:**
- **Job-based execution**: Submit job, get job ID
- **Incremental polling endpoint**: Get only new findings since last poll
- **Two polling modes**:
  1. Standard endpoint with `since` parameter (timestamp or finding ID)
  2. Dedicated incremental endpoint with metadata

**Polling Features:**
- Returns only new findings (not duplicates)
- Metadata: `has_more`, `total_findings`, `new_count`
- Last finding ID/timestamp for next poll
- Thread-safe concurrent access

---

### 14. **Statistics & Analytics** 📊
**Comprehensive statistics:**
- Sites indexed count
- Entities extracted count
- Brand mentions count
- Pages crawled count
- Last crawl timestamp
- URL filter size (BloomFilter)
- Graph statistics (vertices, edges)
- Queue size
- Monitored keywords count

**Activity Reports:**
- Recent activity (last 24 hours)
- High-risk site count
- Category breakdown
- Site discovery timeline

---

### 15. **Advanced Search & Filtering** 🔍
**Powerful query capabilities:**

**Entity Search:**
- Filter by entity type (email, bitcoin, etc.)
- Pattern matching on values
- Context search

**Brand Mention Search:**
- Filter by keyword
- Filter by threat level
- Sort by discovery date

**Site Search:**
- High-risk sites (sorted by risk score)
- Sites by category
- Recent sites
- Clone detection

---

### 16. **Data Structures (Custom DSA)** 🏗️
**Built on custom data structures:**

| Structure | Purpose | Capacity |
|-----------|---------|----------|
| **BloomFilter** | URL deduplication | 10M URLs, 0.1% FP rate |
| **Graph** | Site relationships | Directed graph |
| **HashMap** | Fast lookups | O(1) access |
| **Trie** | Keyword matching | Fast prefix search |
| **MinHeap** | Priority queue | Crawl scheduling |
| **DoublyLinkedList** | Crawl history | Timeline tracking |

---

### 17. **Tor Connectivity Management** 🔐
**Secure Tor integration:**
- Tor proxy connectivity checking
- Exit node verification
- Response time monitoring
- Automatic retry on failures
- Health check before operations

**Configuration:**
- Proxy host/port (default: localhost:9050)
- Proxy type (SOCKS5)
- Timeout settings
- Health check intervals

---

### 18. **Export & Intelligence Reports** 📄
**Data export capabilities:**
- JSON export format
- Complete intelligence dump
- Statistics included
- Sites, mentions, entities
- Timestamps and metadata

---

## API Endpoints

### Job Management
- `POST /api/v1/capabilities/jobs` - Submit dark web intelligence job
- `GET /api/v1/capabilities/jobs/{job_id}` - Get job status
- `GET /api/v1/capabilities/jobs` - List all jobs

### Findings Retrieval
- `GET /api/v1/capabilities/jobs/{job_id}/findings` - Get findings (with `since` parameter for incremental)
- `GET /api/v1/capabilities/jobs/{job_id}/findings/incremental` - Incremental polling endpoint
- `GET /api/v1/capabilities/jobs/{job_id}/findings/stream` - Server-Sent Events streaming

---

## Configuration Options

```python
# Parallel Processing
DARKWEB_MAX_WORKERS = 5              # Thread pool size
DARKWEB_DISCOVERY_TIMEOUT = 300       # 5 min per engine
DARKWEB_CRAWL_TIMEOUT = 600           # 10 min per batch
DARKWEB_BATCH_SIZE = 5                # URLs per batch

# Tor Settings
TOR_PROXY_HOST = "localhost"
TOR_PROXY_PORT = 9050
TOR_PROXY_TYPE = "socks5h"
TOR_TIMEOUT = 30

# Crawler Settings
CRAWLER_SCORE_CATEGORIE = 20          # Min category score
CRAWLER_SCORE_KEYWORDS = 40           # Min keyword score
CRAWLER_COUNT_CATEGORIES = 5          # Max retry count
```

---

## Use Cases

1. **Brand Protection**: Monitor for brand mentions, impersonation, fake sites
2. **Data Leak Detection**: Find leaked credentials, emails, credit cards
3. **Threat Intelligence**: Track ransomware groups, hacking forums
4. **Fraud Detection**: Identify carding sites, counterfeit operations
5. **Competitive Intelligence**: Monitor competitor mentions
6. **Security Research**: Analyze dark web ecosystem and trends

---

## Performance Metrics

- **URL Discovery**: 5-6 engines in parallel (~5-6x speedup)
- **Site Crawling**: 5 workers in parallel (~3-5x speedup)
- **Total Processing**: 1-3 minutes for 10 URLs (vs 5-10 minutes sequential)
- **BloomFilter**: 10M capacity with 0.1% false positive rate
- **Memory Efficient**: Custom DSA structures optimized for security workloads

---

## Security Features

- All traffic routed through Tor proxy
- No direct connections to .onion sites
- User agent randomization
- Request timeouts to prevent hanging
- Thread-safe concurrent operations
- Error isolation (one failure doesn't stop batch)

---

## Integration Points

- **Orchestrator**: Job management and execution
- **Risk Engine**: Risk score calculation
- **Graph Engine**: Relationship correlation
- **Notification Service**: Alert generation
- **Report Generator**: Intelligence reports

---

## Future Enhancements (Potential)

- Machine learning for content classification
- Image analysis for site screenshots
- Blockchain transaction tracking
- Automated threat actor profiling
- Integration with threat intelligence feeds
- Real-time alerting via WebSocket
