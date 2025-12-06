"""
Web Reconnaissance Collector

Inspired by: oxdork, lookyloo
Purpose: Asset discovery through dorking and domain analysis.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from datetime import datetime
import httpx
from loguru import logger

from app.core.dsa import Trie, HashMap, BloomFilter


class WebRecon:
    """
    Web Reconnaissance Collector.
    
    Features:
    - Google dork query generation
    - Subdomain enumeration
    - Asset discovery
    - Third-party dependency mapping
    
    DSA Usage:
    - Trie: Dork pattern matching
    - HashMap: Asset caching
    - BloomFilter: URL deduplication
    """
    
    # Common dork patterns
    DORK_PATTERNS = [
        'site:{domain} filetype:pdf',
        'site:{domain} filetype:doc',
        'site:{domain} filetype:xls',
        'site:{domain} filetype:sql',
        'site:{domain} filetype:log',
        'site:{domain} filetype:env',
        'site:{domain} inurl:admin',
        'site:{domain} inurl:login',
        'site:{domain} inurl:backup',
        'site:{domain} inurl:config',
        'site:{domain} intitle:"index of"',
        'site:{domain} ext:conf',
        'site:{domain} ext:bak',
        'site:{domain} "password" filetype:txt',
        'site:{domain} "api_key" OR "apikey"',
    ]
    
    def __init__(self):
        """Initialize Web Recon collector."""
        self._dork_trie = Trie()
        self._asset_cache = HashMap()
        self._seen_urls = BloomFilter(expected_items=100000)
        self._results = []
        
        # Initialize dork patterns
        for pattern in self.DORK_PATTERNS:
            self._dork_trie.insert(pattern, pattern)
    
    async def discover_assets(self, domain: str) -> Dict[str, Any]:
        """Discover assets for a domain.
        
        Args:
            domain: Target domain
            
        Returns:
            Discovery results
        """
        logger.info(f"Starting asset discovery for {domain}")
        
        results = {
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
            "subdomains": [],
            "endpoints": [],
            "files": [],
            "technologies": [],
            "third_parties": []
        }
        
        # Generate dorks for this domain
        dorks = self.generate_dorks(domain)
        results["dorks_generated"] = len(dorks)
        
        # Discover subdomains
        subdomains = await self._enumerate_subdomains(domain)
        results["subdomains"] = subdomains
        
        # Check common endpoints
        endpoints = await self._check_endpoints(domain)
        results["endpoints"] = endpoints
        
        # Cache results
        self._asset_cache.put(domain, results)
        
        return results
    
    def generate_dorks(self, domain: str) -> List[str]:
        """Generate dork queries for a domain.
        
        Args:
            domain: Target domain
            
        Returns:
            List of dork queries
        """
        dorks = []
        
        for pattern in self.DORK_PATTERNS:
            dork = pattern.format(domain=domain)
            dorks.append(dork)
        
        return dorks
    
    async def _enumerate_subdomains(self, domain: str) -> List[Dict[str, Any]]:
        """Enumerate subdomains.
        
        Args:
            domain: Target domain
            
        Returns:
            List of discovered subdomains
        """
        subdomains = []
        
        # Common subdomain prefixes
        common_prefixes = [
            'www', 'mail', 'remote', 'blog', 'webmail', 'server',
            'ns1', 'ns2', 'smtp', 'secure', 'vpn', 'api', 'dev',
            'staging', 'test', 'portal', 'admin', 'app', 'cdn',
            'static', 'assets', 'img', 'images', 'docs', 'help',
            'support', 'status', 'monitor', 'jenkins', 'gitlab',
            'git', 'svn', 'ftp', 'sftp', 'ssh', 'cpanel', 'panel'
        ]
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for prefix in common_prefixes:
                subdomain = f"{prefix}.{domain}"
                
                # Skip if already seen
                if self._seen_urls.contains(subdomain):
                    continue
                self._seen_urls.add(subdomain)
                
                try:
                    response = await client.get(f"https://{subdomain}", follow_redirects=False)
                    subdomains.append({
                        "subdomain": subdomain,
                        "status": response.status_code,
                        "https": True
                    })
                except:
                    try:
                        response = await client.get(f"http://{subdomain}", follow_redirects=False)
                        subdomains.append({
                            "subdomain": subdomain,
                            "status": response.status_code,
                            "https": False
                        })
                    except:
                        pass
        
        return subdomains
    
    async def _check_endpoints(self, domain: str) -> List[Dict[str, Any]]:
        """Check common endpoints.
        
        Args:
            domain: Target domain
            
        Returns:
            List of discovered endpoints
        """
        endpoints = []
        
        # Common sensitive endpoints
        paths = [
            '/.git/config', '/.env', '/robots.txt', '/sitemap.xml',
            '/admin', '/login', '/api', '/api/v1', '/swagger',
            '/docs', '/.well-known/security.txt', '/wp-admin',
            '/phpinfo.php', '/server-status', '/backup', '/config',
            '/.htaccess', '/web.config', '/.svn/entries'
        ]
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for path in paths:
                url = f"https://{domain}{path}"
                
                try:
                    response = await client.get(url, follow_redirects=False)
                    if response.status_code != 404:
                        endpoints.append({
                            "path": path,
                            "url": url,
                            "status": response.status_code,
                            "content_length": len(response.content)
                        })
                except:
                    pass
        
        return endpoints
    
    def get_cached_results(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get cached results for a domain.
        
        Args:
            domain: Target domain
            
        Returns:
            Cached results or None
        """
        return self._asset_cache.get(domain)
    
    def stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        return {
            "dork_patterns": len(self.DORK_PATTERNS),
            "cached_domains": len(self._asset_cache),
            "seen_urls": self._seen_urls.stats()
        }


