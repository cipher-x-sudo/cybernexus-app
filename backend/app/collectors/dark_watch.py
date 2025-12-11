"""
DarkWatch Collector - Dark Web Monitoring & Crawling

Inspired by: freshonions-torscraper (https://github.com/dirtyfilthy/freshonions-torscraper)

This collector monitors dark web (.onion) sites for:
- Brand mentions and impersonation
- Leaked credentials and data
- Threat actor discussions
- Malware marketplaces
- Cryptocurrency transactions

Uses Bloom Filter for efficient duplicate detection and Graph for relationship mapping.

Features:
- Onion site discovery and indexing
- Content extraction (emails, bitcoin addresses, SSH keys)
- Brand/keyword monitoring
- Site fingerprinting and clone detection
- Language detection
- Risk scoring based on content
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import re
import json

# Import our custom DSA
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dsa.graph import Graph
from core.dsa.bloom_filter import BloomFilter
from core.dsa.hashmap import HashMap
from core.dsa.trie import Trie
from core.dsa.linked_list import DoublyLinkedList
from core.dsa.heap import MinHeap

# Import dark web crawlers and extractors
from app.collectors.darkwatch_modules.crawlers.tor_connector import TorConnector
from app.collectors.darkwatch_modules.crawlers.url_database import URLDatabase
from app.collectors.darkwatch_modules.crawlers.discovery_engines import (
    GistEngine, RedditEngine, SecurityNewsEngine,
    DarkWebEngine, SearchEngine, PastebinEngine
)
from app.collectors.darkwatch_modules.extractors.site_crawler import crawl_onion_site, extract_entities as extract_entities_from_content
from app.collectors.darkwatch_modules.extractors.utils import (
    email_util, bitcoin_util, language_detector
)
from app.config import settings
from loguru import logger
import time


class SiteCategory(Enum):
    """Categories of dark web sites"""
    MARKETPLACE = "marketplace"
    FORUM = "forum"
    LEAK_SITE = "leak_site"
    RANSOMWARE = "ransomware"
    CARDING = "carding"
    DRUGS = "drugs"
    HACKING = "hacking"
    FRAUD = "fraud"
    CRYPTO = "cryptocurrency"
    WEAPONS = "weapons"
    COUNTERFEIT = "counterfeit"
    HOSTING = "hosting"
    SEARCH = "search_engine"
    SOCIAL = "social_media"
    NEWS = "news"
    UNKNOWN = "unknown"


class ThreatLevel(Enum):
    """Threat severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ExtractedEntity:
    """Entity extracted from dark web content"""
    entity_type: str  # email, bitcoin, ssh_key, phone, etc.
    value: str
    context: str  # Surrounding text
    source_url: str
    discovered_at: datetime
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "type": self.entity_type,
            "value": self.value,
            "context": self.context[:200] if self.context else "",
            "source_url": self.source_url,
            "discovered_at": self.discovered_at.isoformat(),
            "confidence": self.confidence
        }


@dataclass
class OnionSite:
    """Represents a dark web .onion site"""
    onion_url: str
    site_id: str
    title: str
    category: SiteCategory
    first_seen: datetime
    last_seen: datetime
    is_online: bool
    language: str
    content_hash: str
    page_count: int = 1
    linked_sites: List[str] = field(default_factory=list)
    extracted_entities: List[ExtractedEntity] = field(default_factory=list)
    keywords_matched: List[str] = field(default_factory=list)
    threat_level: ThreatLevel = ThreatLevel.INFO
    risk_score: float = 0.0
    ssh_fingerprints: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "site_id": self.site_id,
            "onion_url": self.onion_url,
            "title": self.title,
            "category": self.category.value,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "is_online": self.is_online,
            "language": self.language,
            "page_count": self.page_count,
            "linked_sites_count": len(self.linked_sites),
            "entities_count": len(self.extracted_entities),
            "keywords_matched": self.keywords_matched,
            "threat_level": self.threat_level.value,
            "risk_score": self.risk_score
        }


@dataclass
class BrandMention:
    """Brand or keyword mention on dark web"""
    mention_id: str
    keyword: str
    context: str
    source_site: str
    source_url: str
    discovered_at: datetime
    threat_level: ThreatLevel
    is_impersonation: bool = False
    is_data_leak: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "mention_id": self.mention_id,
            "keyword": self.keyword,
            "context": self.context[:300],
            "source_site": self.source_site,
            "source_url": self.source_url,
            "discovered_at": self.discovered_at.isoformat(),
            "threat_level": self.threat_level.value,
            "is_impersonation": self.is_impersonation,
            "is_data_leak": self.is_data_leak
        }


@dataclass
class CrawlJob:
    """Scheduled crawl job"""
    job_id: str
    target_url: str
    priority: int  # Lower = higher priority
    scheduled_at: datetime
    depth: int = 1
    extract_entities: bool = True
    
    def __lt__(self, other):
        return self.priority < other.priority


class DarkWatch:
    """
    Dark Web Monitoring Collector
    
    Monitors and analyzes dark web content for threat intelligence.
    Inspired by freshonions-torscraper's approach to onion site indexing.
    
    DSA Usage:
    - BloomFilter: Efficient duplicate URL detection
    - Graph: Site relationship mapping
    - HashMap: Fast lookups for sites, entities, mentions
    - Trie: Keyword/brand matching
    - MinHeap: Priority queue for crawl scheduling
    - DoublyLinkedList: Crawl history timeline
    """
    
    # Regex patterns for entity extraction
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "bitcoin": r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
        "bitcoin_bech32": r'\bbc1[a-zA-HJ-NP-Z0-9]{39,59}\b',
        "monero": r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b',
        "ethereum": r'\b0x[a-fA-F0-9]{40}\b',
        "onion_v2": r'\b[a-z2-7]{16}\.onion\b',
        "onion_v3": r'\b[a-z2-7]{56}\.onion\b',
        "ssh_fingerprint": r'\b(?:SHA256|MD5):[A-Za-z0-9+/=:]{32,64}\b',
        "pgp_key": r'-----BEGIN PGP PUBLIC KEY BLOCK-----',
        "phone": r'\b\+?[1-9]\d{1,14}\b',
        "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        "credit_card": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b',
    }
    
    # Category indicators
    CATEGORY_KEYWORDS = {
        SiteCategory.MARKETPLACE: ["market", "shop", "buy", "sell", "vendor", "escrow"],
        SiteCategory.FORUM: ["forum", "board", "discussion", "thread", "community"],
        SiteCategory.LEAK_SITE: ["leak", "dump", "breach", "database", "combo"],
        SiteCategory.RANSOMWARE: ["ransomware", "decrypt", "ransom", "locked", "encrypted files"],
        SiteCategory.CARDING: ["card", "cvv", "fullz", "dumps", "bins", "cc"],
        SiteCategory.DRUGS: ["drug", "mdma", "cocaine", "cannabis", "pharma"],
        SiteCategory.HACKING: ["hack", "exploit", "0day", "shell", "rat", "botnet"],
        SiteCategory.FRAUD: ["fraud", "scam", "fake", "counterfeit id", "documents"],
        SiteCategory.CRYPTO: ["bitcoin", "crypto", "mixer", "tumbler", "exchange"],
    }
    
    def __init__(self, monitored_keywords: List[str] = None):
        """
        Initialize DarkWatch collector
        
        Args:
            monitored_keywords: Keywords/brands to monitor
        """
        # Bloom filter for URL deduplication (10M expected items, 0.1% FP rate)
        self.url_filter = BloomFilter(expected_items=10_000_000, false_positive_rate=0.001)
        
        # Graph for site relationships
        self.site_graph = Graph(directed=True)
        
        # HashMaps for fast lookups
        self.sites = HashMap()  # site_id -> OnionSite
        self.entities = HashMap()  # entity_value -> ExtractedEntity
        self.mentions = HashMap()  # mention_id -> BrandMention
        
        # Trie for keyword matching
        self.keyword_trie = Trie()
        self.monitored_keywords = monitored_keywords or []
        for keyword in self.monitored_keywords:
            self.keyword_trie.insert(keyword.lower())
        
        # MinHeap for crawl priority queue
        self.crawl_queue = MinHeap()
        
        # Timeline of crawls
        self.crawl_history = DoublyLinkedList()
        
        # Statistics
        self.stats = {
            "sites_indexed": 0,
            "entities_extracted": 0,
            "brand_mentions": 0,
            "pages_crawled": 0,
            "last_crawl": None
        }
    
    def add_monitored_keyword(self, keyword: str):
        """Add a keyword/brand to monitor"""
        self.monitored_keywords.append(keyword)
        self.keyword_trie.insert(keyword.lower())
    
    def _generate_site_id(self, onion_url: str) -> str:
        """Generate unique site ID from URL"""
        return hashlib.sha256(onion_url.encode()).hexdigest()[:16]
    
    def _generate_mention_id(self, keyword: str, url: str) -> str:
        """Generate unique mention ID"""
        data = f"{keyword}:{url}:{datetime.now().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def _hash_content(self, content: str) -> str:
        """Generate content hash for clone detection"""
        # Normalize content for comparison
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def _detect_language(self, text: str) -> str:
        """Detect language using language detector utility."""
        if not text or len(text) < 10:
            return 'unknown'
        
        try:
            return language_detector.detect_language(text)
        except Exception:
            # Fallback to simple detection
            english_words = {'the', 'and', 'is', 'in', 'to', 'of', 'for', 'with'}
            words = set(text.lower().split()[:100])
            scores = {'en': len(words & english_words)}
            return max(scores, key=scores.get) if max(scores.values()) > 0 else 'unknown'
    
    def _categorize_site(self, content: str, title: str) -> SiteCategory:
        """Categorize site based on content analysis"""
        text = f"{title} {content}".lower()
        
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        return SiteCategory.UNKNOWN
    
    def _extract_entities(self, content: str, source_url: str) -> List[ExtractedEntity]:
        """Extract entities from content using regex patterns"""
        entities = []
        
        for entity_type, pattern in self.PATTERNS.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                value = match.group()
                
                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end]
                
                entity = ExtractedEntity(
                    entity_type=entity_type,
                    value=value,
                    context=context,
                    source_url=source_url,
                    discovered_at=datetime.now()
                )
                entities.append(entity)
                
                # Cache entity
                self.entities.put(value, entity)
        
        return entities
    
    def _extract_onion_links(self, content: str) -> List[str]:
        """Extract .onion links from content"""
        v2_pattern = r'[a-z2-7]{16}\.onion'
        v3_pattern = r'[a-z2-7]{56}\.onion'
        
        links = []
        for match in re.finditer(v2_pattern, content):
            links.append(f"http://{match.group()}")
        for match in re.finditer(v3_pattern, content):
            links.append(f"http://{match.group()}")
        
        return list(set(links))
    
    def _calculate_risk_score(
        self,
        category: SiteCategory,
        entities: List[ExtractedEntity],
        keywords_matched: List[str]
    ) -> Tuple[float, ThreatLevel]:
        """Calculate risk score and threat level"""
        score = 0.0
        
        # Category-based scoring
        category_scores = {
            SiteCategory.RANSOMWARE: 0.9,
            SiteCategory.LEAK_SITE: 0.85,
            SiteCategory.CARDING: 0.8,
            SiteCategory.HACKING: 0.75,
            SiteCategory.FRAUD: 0.7,
            SiteCategory.MARKETPLACE: 0.6,
            SiteCategory.DRUGS: 0.5,
            SiteCategory.WEAPONS: 0.5,
            SiteCategory.FORUM: 0.4,
            SiteCategory.UNKNOWN: 0.3,
        }
        score += category_scores.get(category, 0.3)
        
        # Entity-based scoring
        entity_weights = {
            "credit_card": 0.3,
            "email": 0.1,
            "bitcoin": 0.05,
            "ssh_fingerprint": 0.15,
            "pgp_key": 0.05,
        }
        for entity in entities:
            score += entity_weights.get(entity.entity_type, 0.02)
        
        # Keyword match scoring (brand mentions)
        score += len(keywords_matched) * 0.15
        
        # Cap at 1.0
        score = min(score, 1.0)
        
        # Determine threat level
        if score >= 0.8:
            level = ThreatLevel.CRITICAL
        elif score >= 0.6:
            level = ThreatLevel.HIGH
        elif score >= 0.4:
            level = ThreatLevel.MEDIUM
        elif score >= 0.2:
            level = ThreatLevel.LOW
        else:
            level = ThreatLevel.INFO
        
        return score, level
    
    def _check_keyword_matches(self, content: str) -> List[str]:
        """Check content against monitored keywords"""
        matches = []
        content_lower = content.lower()
        
        for keyword in self.monitored_keywords:
            if keyword.lower() in content_lower:
                matches.append(keyword)
        
        return matches
    
    def _crawl_site_real(self, onion_url: str) -> Dict[str, Any]:
        """
        Crawl onion site using real tools.
        
        Args:
            onion_url: The .onion URL to crawl
            
        Returns:
            Dictionary with site data
        """
        # Use keyword-focused crawler if keywords are monitored
        if self.monitored_keywords:
            return self._crawl_with_keyword_monitor(onion_url)
        else:
            # Use comprehensive site analyzer
            return self._crawl_with_site_analyzer(onion_url)
    
    def _crawl_with_keyword_monitor(self, onion_url: str) -> Dict[str, Any]:
        """
        Crawl using keyword-focused approach.
        
        Args:
            onion_url: URL to crawl
            
        Returns:
            Dictionary with site data
        """
        crawl_start_time = time.time()
        logger.info(f"[DarkWatch] Starting keyword monitor crawl for {onion_url}")
        
        try:
            # Initialize TorConnector
            logger.debug(f"[DarkWatch] Initializing TorConnector for {onion_url}")
            connector = TorConnector(
                proxy_host=settings.TOR_PROXY_HOST,
                proxy_port=settings.TOR_PROXY_PORT,
                proxy_type=settings.TOR_PROXY_TYPE,
                timeout=settings.TOR_TIMEOUT,
                score_categorie=settings.CRAWLER_SCORE_CATEGORIE,
                score_keywords=settings.CRAWLER_SCORE_KEYWORDS,
                count_categories=settings.CRAWLER_COUNT_CATEGORIES,
                db_path=str(settings.DATA_DIR / settings.CRAWLER_DB_PATH),
                db_name=settings.CRAWLER_DB_NAME
            )
            
            # Check if URL exists in database
            logger.debug(f"[DarkWatch] Checking database for {onion_url}")
            db_check_start = time.time()
            url_data = connector.database.select_url(url=onion_url)
            db_check_time = time.time() - db_check_start
            
            if not url_data:
                logger.debug(f"[DarkWatch] URL not in database, saving {onion_url}")
                connector.database.save(
                    url=onion_url,
                    source="Script",
                    type="URI",
                    baseurl=onion_url
                )
                url_data = connector.database.select_url(url=onion_url)
            
            if url_data:
                logger.debug(f"[DarkWatch] Starting crawler for URL ID {url_data[0]} (database check took {db_check_time:.2f}s)")
                crawl_start = time.time()
                # Crawl the URL
                result = connector.crawler(url_data[0])
                crawl_time = time.time() - crawl_start
                
                if result.get("status") == "online":
                    keywords_matched = result.get("keywords_matched", "")
                    logger.debug(f"[DarkWatch] Crawl completed for {onion_url} in {crawl_time:.2f}s - Status: online, Keywords matched: {keywords_matched}, Score: {result.get('score_keywords', 0)}")
                    return {
                        "title": result.get("title", "Untitled"),
                        "content": result.get("content", ""),
                        "category": self._map_category_from_string(result.get("category", "unknown")),
                        "linked_onions": connector.more_urls(onion_url) or [],
                        "keywords_matched": result.get("keywords_matched", ""),
                        "score_categorie": result.get("score_categorie", 0),
                        "score_keywords": result.get("score_keywords", 0)
                    }
                else:
                    logger.debug(f"[DarkWatch] Crawl completed for {onion_url} in {crawl_time:.2f}s - Status: {result.get('status', 'unknown')}")
        
        except Exception as e:
            crawl_error_time = time.time() - crawl_start_time
            logger.error(f"[DarkWatch] Error in keyword monitor crawl for {onion_url} after {crawl_error_time:.2f}s: {e}", exc_info=True)
        
        # Fallback to site analyzer
        logger.debug(f"[DarkWatch] Falling back to site analyzer for {onion_url}")
        return self._crawl_with_site_analyzer(onion_url)
    
    def _crawl_with_site_analyzer(self, onion_url: str) -> Dict[str, Any]:
        """
        Crawl using comprehensive site analysis.
        
        Args:
            onion_url: URL to crawl
            
        Returns:
            Dictionary with site data
        """
        crawl_start_time = time.time()
        logger.info(f"[DarkWatch] Starting site analyzer crawl for {onion_url}")
        
        try:
            # Use site_crawler function
            logger.debug(f"[DarkWatch] Calling crawl_onion_site for {onion_url}")
            site_data = crawl_onion_site(
                onion_url,
                proxy_host=settings.TOR_PROXY_HOST,
                proxy_port=settings.TOR_PROXY_PORT,
                proxy_type=settings.TOR_PROXY_TYPE,
                timeout=settings.TOR_TIMEOUT
            )
            crawl_time = time.time() - crawl_start_time
            
            if site_data.get("status") == "online":
                emails_count = len(site_data.get("emails", []))
                bitcoin_count = len(site_data.get("bitcoin_addresses", []))
                links_count = len(site_data.get("links", []))
                logger.debug(f"[DarkWatch] Site analyzer crawl completed for {onion_url} in {crawl_time:.2f}s - Status: online, Emails: {emails_count}, Bitcoin: {bitcoin_count}, Links: {links_count}")
                return {
                    "title": site_data.get("title", "Untitled"),
                    "content": site_data.get("text", ""),
                    "category": self._categorize_site(site_data.get("text", ""), site_data.get("title", "")),
                    "linked_onions": [link.replace("http://", "").replace("https://", "") 
                                     for link in site_data.get("links", []) 
                                     if ".onion" in link],
                    "emails": site_data.get("emails", []),
                    "bitcoin_addresses": site_data.get("bitcoin_addresses", []),
                    "language": site_data.get("language", "unknown")
                }
            else:
                logger.debug(f"[DarkWatch] Site analyzer crawl completed for {onion_url} in {crawl_time:.2f}s - Status: {site_data.get('status', 'unknown')}")
        
        except Exception as e:
            crawl_error_time = time.time() - crawl_start_time
            logger.error(f"[DarkWatch] Error in site analyzer crawl for {onion_url} after {crawl_error_time:.2f}s: {e}", exc_info=True)
        
        return {
            "title": "Unknown",
            "content": "",
            "category": SiteCategory.UNKNOWN,
            "linked_onions": []
        }
    
    def _map_category_from_string(self, category_str: str) -> SiteCategory:
        """Map category string to SiteCategory enum."""
        category_lower = category_str.lower()
        if "market" in category_lower:
            return SiteCategory.MARKETPLACE
        elif "forum" in category_lower:
            return SiteCategory.FORUM
        elif "leak" in category_lower:
            return SiteCategory.LEAK_SITE
        elif "ransom" in category_lower:
            return SiteCategory.RANSOMWARE
        elif "card" in category_lower:
            return SiteCategory.CARDING
        elif "drug" in category_lower:
            return SiteCategory.DRUGS
        elif "hack" in category_lower:
            return SiteCategory.HACKING
        else:
            return SiteCategory.UNKNOWN
    
    def _discover_urls_with_engines(self) -> List[str]:
        """
        Discover URLs using discovery engines.
        
        Returns:
            List of discovered URLs
        """
        urls = []
        
        try:
            # Use each engine
            engines = [
                GistEngine(),
                RedditEngine(),
                SecurityNewsEngine(),
                DarkWebEngine(),
                SearchEngine()
            ]
            
            for engine in engines:
                try:
                    discovered = engine.discover_urls()
                    if discovered:
                        urls.extend(discovered)
                except Exception as e:
                    logger.debug(f"Engine {engine.__class__.__name__} error: {e}")
                    continue
            
            # Store in URLDatabase
            db = URLDatabase(
                dbpath=str(settings.DATA_DIR / settings.CRAWLER_DB_PATH),
                dbname=settings.CRAWLER_DB_NAME
            )
            
            for url in urls:
                if not db.compare(url):
                    db.save(url=url, source="DiscoveryEngine", type="Domain")
        
        except Exception as e:
            logger.error(f"Error discovering URLs: {e}")
        
        return list(set(urls))  # Return unique URLs
    
    def crawl_site(self, onion_url: str, depth: int = 1) -> OnionSite:
        """
        Crawl an onion site and extract intelligence
        
        Args:
            onion_url: The .onion URL to crawl
            depth: How many levels of links to follow
            
        Returns:
            OnionSite with extracted data
        """
        crawl_start_time = time.time()
        logger.info(f"[DarkWatch] crawl_site called for {onion_url} (depth={depth})")
        
        # Check if already crawled recently
        if self.url_filter.contains(onion_url):
            existing = self.sites.get(self._generate_site_id(onion_url))
            if existing:
                logger.debug(f"[DarkWatch] Site {onion_url} already crawled, returning cached result")
                return existing
        
        # Add to bloom filter
        self.url_filter.add(onion_url)
        logger.debug(f"[DarkWatch] Added {onion_url} to URL filter")
        
        # Real crawl
        logger.info(f"[DarkWatch] Starting real crawl for {onion_url}")
        crawl_start = time.time()
        page_data = self._crawl_site_real(onion_url)
        crawl_time = time.time() - crawl_start
        logger.info(f"[DarkWatch] Real crawl completed for {onion_url} in {crawl_time:.2f}s")
        
        site_id = self._generate_site_id(onion_url)
        content = page_data["content"]
        title = page_data["title"]
        content_length = len(content)
        logger.debug(f"[DarkWatch] Extracted data for {onion_url}: Title='{title}', Content length={content_length} chars")
        
        # Extract entities
        entity_extract_start = time.time()
        entities = self._extract_entities(content, onion_url)
        entity_extract_time = time.time() - entity_extract_start
        logger.debug(f"[DarkWatch] Extracted {len(entities)} entities from {onion_url} in {entity_extract_time:.2f}s")
        
        # Create timestamp once (fix for 'now' variable issue)
        now = datetime.now()
        
        # Also extract from site_data if available (from site analyzer)
        if "emails" in page_data:
            email_count = len(page_data["emails"])
            logger.debug(f"[DarkWatch] Adding {email_count} emails from page_data for {onion_url}")
            for email in page_data["emails"]:
                entities.append(ExtractedEntity(
                    entity_type="email",
                    value=email,
                    context=content[:200] if content else "",
                    source_url=onion_url,
                    discovered_at=now,
                    confidence=1.0
                ))
        
        if "bitcoin_addresses" in page_data:
            bitcoin_count = len(page_data["bitcoin_addresses"])
            logger.debug(f"[DarkWatch] Adding {bitcoin_count} bitcoin addresses from page_data for {onion_url}")
            for addr in page_data["bitcoin_addresses"]:
                entities.append(ExtractedEntity(
                    entity_type="bitcoin",
                    value=addr,
                    context=content[:200] if content else "",
                    source_url=onion_url,
                    discovered_at=now,
                    confidence=1.0
                ))
        
        # Extract linked onion sites
        linked_sites = page_data.get("linked_onions", [])
        linked_sites.extend(self._extract_onion_links(content))
        linked_sites = list(set(linked_sites))
        logger.debug(f"[DarkWatch] Found {len(linked_sites)} linked onion sites for {onion_url}")
        
        # Categorize site
        category_start = time.time()
        category = page_data.get("category", self._categorize_site(content, title))
        category_time = time.time() - category_start
        logger.debug(f"[DarkWatch] Categorized {onion_url} as '{category.value}' in {category_time:.3f}s")
        
        # Check keyword matches
        keyword_check_start = time.time()
        keywords_matched = self._check_keyword_matches(content)
        keyword_check_time = time.time() - keyword_check_start
        logger.debug(f"[DarkWatch] Keyword check for {onion_url}: {len(keywords_matched)} matches found in {keyword_check_time:.3f}s - Matches: {keywords_matched}")
        
        # Calculate risk
        risk_calc_start = time.time()
        risk_score, threat_level = self._calculate_risk_score(
            category, entities, keywords_matched
        )
        risk_calc_time = time.time() - risk_calc_start
        logger.debug(f"[DarkWatch] Risk calculation for {onion_url}: Score={risk_score:.2f}, Threat Level={threat_level.value} (calculated in {risk_calc_time:.3f}s)")
        
        # Detect language
        if "language" in page_data and page_data["language"] != "unknown":
            language = page_data["language"]
            logger.debug(f"[DarkWatch] Language for {onion_url} from page_data: {language}")
        else:
            lang_detect_start = time.time()
            language = self._detect_language(content)
            lang_detect_time = time.time() - lang_detect_start
            logger.debug(f"[DarkWatch] Detected language for {onion_url}: {language} (detected in {lang_detect_time:.3f}s)")
        
        # Create site object
        site = OnionSite(
            onion_url=onion_url,
            site_id=site_id,
            title=title,
            category=category,
            first_seen=now,
            last_seen=now,
            is_online=True,
            language=language,
            content_hash=self._hash_content(content),
            linked_sites=linked_sites,
            extracted_entities=entities,
            keywords_matched=keywords_matched,
            threat_level=threat_level,
            risk_score=risk_score
        )
        
        # Store site
        self.sites.put(site_id, site)
        logger.debug(f"[DarkWatch] Stored site {site_id} in sites HashMap")
        
        # Add to graph
        self.site_graph.add_vertex(site_id, {
            "url": onion_url,
            "category": category.value,
            "threat_level": threat_level.value
        })
        logger.debug(f"[DarkWatch] Added vertex {site_id} to site graph")
        
        # Create edges to linked sites
        for linked_url in linked_sites:
            linked_id = self._generate_site_id(linked_url)
            if not self.site_graph.has_vertex(linked_id):
                self.site_graph.add_vertex(linked_id, {"url": linked_url})
            self.site_graph.add_edge(site_id, linked_id, weight=1.0)
            
            # Queue linked sites for crawling
            if depth > 0:
                job = CrawlJob(
                    job_id=f"job_{linked_id}",
                    target_url=linked_url,
                    priority=10 - depth,  # Higher depth = higher priority number = lower priority
                    scheduled_at=datetime.now(),
                    depth=depth - 1
                )
                self.crawl_queue.push(job)
        
        if linked_sites:
            logger.debug(f"[DarkWatch] Added {len(linked_sites)} edges and queued {min(depth, len(linked_sites))} linked sites for crawling")
        
        # Process keyword matches as brand mentions
        for keyword in keywords_matched:
            mention_id = self._generate_mention_id(keyword, onion_url)
            mention = BrandMention(
                mention_id=mention_id,
                keyword=keyword,
                context=content[:500],
                source_site=site_id,
                source_url=onion_url,
                discovered_at=now,
                threat_level=threat_level,
                is_data_leak=category == SiteCategory.LEAK_SITE
            )
            self.mentions.put(mention_id, mention)
            self.stats["brand_mentions"] += 1
        
        if keywords_matched:
            logger.debug(f"[DarkWatch] Created {len(keywords_matched)} brand mentions for {onion_url}")
        
        # Update history
        self.crawl_history.append({
            "site_id": site_id,
            "url": onion_url,
            "timestamp": now.isoformat(),
            "category": category.value
        })
        
        # Update stats
        self.stats["sites_indexed"] += 1
        self.stats["entities_extracted"] += len(entities)
        self.stats["pages_crawled"] += 1
        self.stats["last_crawl"] = now.isoformat()
        
        total_time = time.time() - crawl_start_time
        logger.info(f"[DarkWatch] crawl_site completed for {onion_url} in {total_time:.2f}s - Final stats: Entities={len(entities)}, Keywords={len(keywords_matched)}, Risk={risk_score:.2f}")
        
        return site
    
    def process_crawl_queue(self, max_items: int = 10) -> List[OnionSite]:
        """Process items from the crawl priority queue"""
        results = []
        processed = 0
        
        while not self.crawl_queue.is_empty() and processed < max_items:
            job = self.crawl_queue.pop()
            
            # Skip if already crawled
            if self.url_filter.contains(job.target_url):
                continue
            
            site = self.crawl_site(job.target_url, depth=job.depth)
            results.append(site)
            processed += 1
        
        return results
    
    def search_entities(
        self,
        entity_type: Optional[str] = None,
        value_pattern: Optional[str] = None
    ) -> List[ExtractedEntity]:
        """Search extracted entities"""
        results = []
        
        for key in self.entities.keys():
            entity = self.entities.get(key)
            if entity:
                if entity_type and entity.entity_type != entity_type:
                    continue
                if value_pattern and not re.search(value_pattern, entity.value, re.I):
                    continue
                results.append(entity)
        
        return results
    
    def get_brand_mentions(
        self,
        keyword: Optional[str] = None,
        min_threat_level: ThreatLevel = ThreatLevel.INFO
    ) -> List[BrandMention]:
        """Get brand/keyword mentions"""
        results = []
        level_order = [ThreatLevel.INFO, ThreatLevel.LOW, ThreatLevel.MEDIUM, 
                       ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        min_level_idx = level_order.index(min_threat_level)
        
        for key in self.mentions.keys():
            mention = self.mentions.get(key)
            if mention:
                if keyword and mention.keyword.lower() != keyword.lower():
                    continue
                mention_level_idx = level_order.index(mention.threat_level)
                if mention_level_idx < min_level_idx:
                    continue
                results.append(mention)
        
        return sorted(results, key=lambda m: m.discovered_at, reverse=True)
    
    def get_site_network(self, site_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get network of connected sites for visualization"""
        if not self.site_graph.has_vertex(site_id):
            return {"nodes": [], "edges": []}
        
        # BFS to get connected sites up to depth
        visited = set()
        nodes = []
        edges = []
        queue = [(site_id, 0)]
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            site = self.sites.get(current_id)
            
            if site:
                nodes.append({
                    "id": current_id,
                    "url": site.onion_url,
                    "title": site.title,
                    "category": site.category.value,
                    "threat_level": site.threat_level.value,
                    "risk_score": site.risk_score
                })
            else:
                # Site discovered via link but not crawled
                vertex_data = self.site_graph.get_vertex_data(current_id)
                nodes.append({
                    "id": current_id,
                    "url": vertex_data.get("url", "unknown") if vertex_data else "unknown",
                    "title": "Not crawled",
                    "category": "unknown",
                    "threat_level": "info",
                    "risk_score": 0
                })
            
            # Get connected sites
            neighbors = self.site_graph.get_neighbors(current_id)
            for neighbor_id, _ in neighbors:
                edges.append({
                    "source": current_id,
                    "target": neighbor_id
                })
                if neighbor_id not in visited:
                    queue.append((neighbor_id, current_depth + 1))
        
        return {"nodes": nodes, "edges": edges}
    
    def find_clones(self, site_id: str) -> List[OnionSite]:
        """Find sites with similar content (potential clones)"""
        target_site = self.sites.get(site_id)
        if not target_site:
            return []
        
        clones = []
        target_hash = target_site.content_hash
        
        for key in self.sites.keys():
            if key == site_id:
                continue
            site = self.sites.get(key)
            if site and site.content_hash == target_hash:
                clones.append(site)
        
        return clones
    
    def get_high_risk_sites(self, limit: int = 20) -> List[OnionSite]:
        """Get sites with highest risk scores"""
        sites = []
        for key in self.sites.keys():
            site = self.sites.get(key)
            if site:
                sites.append(site)
        
        return sorted(sites, key=lambda s: s.risk_score, reverse=True)[:limit]
    
    def get_recent_activity(self, hours: int = 24) -> Dict[str, Any]:
        """Get recent crawling activity"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_sites = []
        recent_mentions = []
        recent_entities = []
        
        for key in self.sites.keys():
            site = self.sites.get(key)
            if site and site.last_seen >= cutoff:
                recent_sites.append(site)
        
        for key in self.mentions.keys():
            mention = self.mentions.get(key)
            if mention and mention.discovered_at >= cutoff:
                recent_mentions.append(mention)
        
        return {
            "period_hours": hours,
            "sites_discovered": len(recent_sites),
            "brand_mentions": len(recent_mentions),
            "high_risk_count": len([s for s in recent_sites if s.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]]),
            "categories": self._count_categories(recent_sites)
        }
    
    def _count_categories(self, sites: List[OnionSite]) -> Dict[str, int]:
        """Count sites by category"""
        counts = {}
        for site in sites:
            cat = site.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics"""
        return {
            **self.stats,
            "url_filter_size": self.url_filter.count,
            "graph_sites": self.site_graph.vertex_count(),
            "graph_connections": self.site_graph.edge_count(),
            "queue_size": len(self.crawl_queue),
            "monitored_keywords": len(self.monitored_keywords)
        }
    
    def export_intel(self, format: str = "json") -> str:
        """Export collected intelligence"""
        data = {
            "exported_at": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "sites": [self.sites.get(k).to_dict() for k in self.sites.keys() if self.sites.get(k)],
            "mentions": [self.mentions.get(k).to_dict() for k in self.mentions.keys() if self.mentions.get(k)],
            "entities_sample": [self.entities.get(k).to_dict() for k in list(self.entities.keys())[:100] if self.entities.get(k)]
        }
        return json.dumps(data, indent=2)


# Example usage
if __name__ == "__main__":
    # Initialize with monitored keywords
    collector = DarkWatch(monitored_keywords=["MyCorp", "example.com", "CEO Name"])
    
    # Crawl some sites
    site1 = collector.crawl_site("http://darkmarket" + "a" * 10 + ".onion")
    print(f"Crawled: {site1.title}")
    print(f"Category: {site1.category.value}")
    print(f"Threat Level: {site1.threat_level.value}")
    print(f"Entities found: {len(site1.extracted_entities)}")
    
    # Process queue
    additional = collector.process_crawl_queue(max_items=5)
    print(f"\nProcessed {len(additional)} additional sites from queue")
    
    # Get statistics
    print(f"\nStatistics: {collector.get_statistics()}")


