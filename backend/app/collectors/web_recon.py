"""
Web Reconnaissance Collector

Inspired by: oxdork, lookyloo
Purpose: Asset discovery through dorking and domain analysis.
"""

import asyncio
import re
import socket
from typing import Any, Dict, List, Optional, Callable
from urllib.parse import urlparse, urljoin
from datetime import datetime
import httpx
from loguru import logger

from app.core.dsa import Trie, HashMap, BloomFilter


class WebRecon:
    """
    Enhanced Web Reconnaissance Collector.
    
    Features:
    - Comprehensive Google dork query generation (50+ patterns)
    - Advanced subdomain enumeration
    - Deep file detection and verification
    - Endpoint discovery (admin panels, APIs, docs)
    - Source code exposure detection (.git, .svn, etc.)
    - Configuration file scanning
    - Structured findings with categories
    
    DSA Usage:
    - Trie: Dork pattern matching
    - HashMap: Asset caching
    - BloomFilter: URL deduplication
    """
    
    # Extended dork patterns (50+ patterns)
    DORK_PATTERNS = [
        # Sensitive files
        'site:{domain} filetype:env',
        'site:{domain} filetype:config',
        'site:{domain} filetype:key',
        'site:{domain} filetype:pem',
        'site:{domain} filetype:p12',
        'site:{domain} filetype:pfx',
        'site:{domain} filetype:cer',
        'site:{domain} filetype:jks',
        'site:{domain} "API_KEY" OR "api_key" OR "apikey"',
        'site:{domain} "SECRET" OR "secret_key" OR "secret"',
        'site:{domain} "password" filetype:txt',
        'site:{domain} "password" filetype:env',
        'site:{domain} "token" filetype:env',
        'site:{domain} "credentials" filetype:txt',
        'site:{domain} "aws_access_key" OR "aws_secret"',
        'site:{domain} "github_token" OR "gitlab_token"',
        # Database files
        'site:{domain} filetype:sql',
        'site:{domain} filetype:db',
        'site:{domain} filetype:sqlite',
        'site:{domain} filetype:mdb',
        'site:{domain} filetype:accdb',
        'site:{domain} "database" filetype:sql',
        # Backup files
        'site:{domain} filetype:bak',
        'site:{domain} filetype:backup',
        'site:{domain} filetype:old',
        'site:{domain} filetype:tar.gz',
        'site:{domain} filetype:zip',
        'site:{domain} filetype:rar',
        'site:{domain} intitle:"index of" backup',
        'site:{domain} intitle:"index of" dump',
        # Documents
        'site:{domain} filetype:pdf',
        'site:{domain} filetype:doc',
        'site:{domain} filetype:docx',
        'site:{domain} filetype:xls',
        'site:{domain} filetype:xlsx',
        'site:{domain} filetype:ppt',
        'site:{domain} filetype:pptx',
        # Log files
        'site:{domain} filetype:log',
        'site:{domain} filetype:txt "error"',
        'site:{domain} filetype:log "password"',
        # Admin panels and login pages
        'site:{domain} inurl:admin',
        'site:{domain} inurl:login',
        'site:{domain} inurl:administrator',
        'site:{domain} inurl:wp-admin',
        'site:{domain} inurl:phpmyadmin',
        'site:{domain} inurl:panel',
        'site:{domain} inurl:cpanel',
        'site:{domain} intitle:"admin login"',
        'site:{domain} intitle:"login" inurl:admin',
        # API endpoints
        'site:{domain} inurl:api',
        'site:{domain} inurl:api/v1',
        'site:{domain} inurl:graphql',
        'site:{domain} inurl:swagger',
        'site:{domain} inurl:openapi',
        'site:{domain} filetype:json "api"',
        # Source code repositories
        'site:{domain} inurl:.git',
        'site:{domain} inurl:.svn',
        'site:{domain} inurl:.hg',
        'site:{domain} filetype:git',
        'site:{domain} "git clone"',
        # Configuration files
        'site:{domain} filetype:conf',
        'site:{domain} filetype:ini',
        'site:{domain} filetype:xml',
        'site:{domain} filetype:yaml',
        'site:{domain} filetype:yml',
        'site:{domain} inurl:config',
        'site:{domain} inurl:settings',
        'site:{domain} inurl:web.config',
        'site:{domain} inurl:.htaccess',
        # Directory listings
        'site:{domain} intitle:"index of"',
        'site:{domain} intitle:"directory listing"',
        'site:{domain} intitle:"parent directory"',
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
    
    async def _resolve_dns(self, hostname: str, timeout: float = 2.0) -> bool:
        """Check if a hostname resolves via DNS.
        
        Args:
            hostname: Hostname to resolve
            timeout: DNS resolution timeout in seconds
            
        Returns:
            True if hostname resolves, False otherwise
        """
        try:
            # Use asyncio to run DNS resolution in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
                ),
                timeout=timeout
            )
            return True
        except (socket.gaierror, asyncio.TimeoutError, OSError):
            return False
        except Exception:
            return False
    
    async def discover_assets(
        self, 
        domain: str, 
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """Discover assets for a domain with comprehensive scanning.
        
        Args:
            domain: Target domain
            progress_callback: Optional callback for progress updates (progress, message)
            
        Returns:
            Discovery results with categorized findings
        """
        import time
        discovery_start = time.time()
        logger.info(f"[WebRecon] [domain={domain}] Starting comprehensive asset discovery")
        logger.info(f"[WebRecon] [domain={domain}] Initializing discovery with progress_callback={progress_callback is not None}")
        
        results = {
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
            "subdomains": [],
            "endpoints": [],
            "files": [],
            "source_code": [],
            "admin_panels": [],
            "configs": [],
            "technologies": [],
            "third_parties": []
        }
        
        try:
            if progress_callback:
                logger.info(f"[WebRecon] [domain={domain}] Calling progress_callback(5, 'Initializing discovery...')")
                progress_callback(5, "Initializing discovery...")
            
            # Generate dorks for this domain
            dork_start = time.time()
            logger.info(f"[WebRecon] [domain={domain}] Generating dork queries...")
            dorks = self.generate_dorks(domain)
            dork_time = time.time() - dork_start
            results["dorks_generated"] = len(dorks)
            logger.info(f"[WebRecon] [domain={domain}] Generated {len(dorks)} dork queries in {dork_time:.3f}s")
            logger.info(f"[WebRecon] [domain={domain}] Sample dorks (first 3): {dorks[:3]}")
            
            if progress_callback:
                logger.info(f"[WebRecon] [domain={domain}] Calling progress_callback(10, 'Enumerating subdomains...')")
                progress_callback(10, "Enumerating subdomains...")
            
            # Discover subdomains
            subdomain_start = time.time()
            logger.info(f"[WebRecon] [domain={domain}] Starting subdomain enumeration...")
            try:
                subdomains = await self._enumerate_subdomains(domain)
                subdomain_time = time.time() - subdomain_start
                results["subdomains"] = subdomains
                logger.info(f"[WebRecon] [domain={domain}] Discovered {len(subdomains)} subdomains in {subdomain_time:.3f}s")
                if subdomains:
                    logger.info(f"[WebRecon] [domain={domain}] Sample subdomains (first 5): {[s.get('subdomain') for s in subdomains[:5]]}")
            except Exception as e:
                subdomain_time = time.time() - subdomain_start
                logger.error(f"[WebRecon] [domain={domain}] Subdomain enumeration failed after {subdomain_time:.3f}s: {e}", exc_info=True)
                results["subdomains"] = []
            
            if progress_callback:
                logger.info(f"[WebRecon] [domain={domain}] Calling progress_callback(30, 'Scanning endpoints...')")
                progress_callback(30, "Scanning endpoints...")
            
            # Check common endpoints
            endpoint_start = time.time()
            logger.info(f"[WebRecon] [domain={domain}] Starting endpoint scanning...")
            try:
                endpoints = await self._check_endpoints(domain)
                endpoint_time = time.time() - endpoint_start
                results["endpoints"] = endpoints
                logger.info(f"[WebRecon] [domain={domain}] Discovered {len(endpoints)} endpoints in {endpoint_time:.3f}s")
                if endpoints:
                    logger.info(f"[WebRecon] [domain={domain}] Sample endpoints (first 5): {[e.get('path') for e in endpoints[:5]]}")
            except Exception as e:
                endpoint_time = time.time() - endpoint_start
                logger.error(f"[WebRecon] [domain={domain}] Endpoint scanning failed after {endpoint_time:.3f}s: {e}", exc_info=True)
                results["endpoints"] = []
            
            if progress_callback:
                logger.info(f"[WebRecon] [domain={domain}] Calling progress_callback(50, 'Detecting sensitive files...')")
                progress_callback(50, "Detecting sensitive files...")
            
            # Deep file detection
            file_start = time.time()
            logger.info(f"[WebRecon] [domain={domain}] Starting sensitive file detection...")
            try:
                files = await self._detect_sensitive_files(domain)
                file_time = time.time() - file_start
                results["files"] = files
                logger.info(f"[WebRecon] [domain={domain}] Detected {len(files)} sensitive files in {file_time:.3f}s")
                if files:
                    logger.info(f"[WebRecon] [domain={domain}] Sample files (first 5): {[f.get('path') for f in files[:5]]}")
            except Exception as e:
                file_time = time.time() - file_start
                logger.error(f"[WebRecon] [domain={domain}] Sensitive file detection failed after {file_time:.3f}s: {e}", exc_info=True)
                results["files"] = []
            
            if progress_callback:
                logger.info(f"[WebRecon] [domain={domain}] Calling progress_callback(65, 'Checking for source code exposure...')")
                progress_callback(65, "Checking for source code exposure...")
            
            # Source code exposure detection
            source_start = time.time()
            logger.info(f"[WebRecon] [domain={domain}] Starting source code exposure detection...")
            try:
                source_code = await self._detect_source_code_exposure(domain)
                source_time = time.time() - source_start
                results["source_code"] = source_code
                logger.info(f"[WebRecon] [domain={domain}] Found {len(source_code)} source code exposures in {source_time:.3f}s")
                if source_code:
                    logger.info(f"[WebRecon] [domain={domain}] Source code exposures: {[s.get('type') + ':' + s.get('path') for s in source_code]}")
            except Exception as e:
                source_time = time.time() - source_start
                logger.error(f"[WebRecon] [domain={domain}] Source code detection failed after {source_time:.3f}s: {e}", exc_info=True)
                results["source_code"] = []
            
            if progress_callback:
                logger.info(f"[WebRecon] [domain={domain}] Calling progress_callback(75, 'Scanning admin panels...')")
                progress_callback(75, "Scanning admin panels...")
            
            # Admin panel discovery
            admin_start = time.time()
            logger.info(f"[WebRecon] [domain={domain}] Starting admin panel discovery...")
            try:
                admin_panels = await self._discover_admin_panels(domain)
                admin_time = time.time() - admin_start
                results["admin_panels"] = admin_panels
                logger.info(f"[WebRecon] [domain={domain}] Discovered {len(admin_panels)} admin panels in {admin_time:.3f}s")
                if admin_panels:
                    logger.info(f"[WebRecon] [domain={domain}] Admin panels: {[p.get('name') + ':' + p.get('path') for p in admin_panels]}")
            except Exception as e:
                admin_time = time.time() - admin_start
                logger.error(f"[WebRecon] [domain={domain}] Admin panel discovery failed after {admin_time:.3f}s: {e}", exc_info=True)
                results["admin_panels"] = []
            
            if progress_callback:
                logger.info(f"[WebRecon] [domain={domain}] Calling progress_callback(85, 'Checking configuration files...')")
                progress_callback(85, "Checking configuration files...")
            
            # Configuration file detection
            config_start = time.time()
            logger.info(f"[WebRecon] [domain={domain}] Starting configuration file detection...")
            try:
                configs = await self._detect_config_files(domain)
                config_time = time.time() - config_start
                results["configs"] = configs
                logger.info(f"[WebRecon] [domain={domain}] Found {len(configs)} configuration files in {config_time:.3f}s")
                if configs:
                    logger.info(f"[WebRecon] [domain={domain}] Config files: {[c.get('path') for c in configs[:5]]}")
            except Exception as e:
                config_time = time.time() - config_start
                logger.error(f"[WebRecon] [domain={domain}] Config file detection failed after {config_time:.3f}s: {e}", exc_info=True)
                results["configs"] = []
            
            if progress_callback:
                logger.info(f"[WebRecon] [domain={domain}] Calling progress_callback(95, 'Finalizing results...')")
                progress_callback(95, "Finalizing results...")
            
            # Cache results
            cache_start = time.time()
            logger.info(f"[WebRecon] [domain={domain}] Caching results...")
            self._asset_cache.put(domain, results)
            cache_time = time.time() - cache_start
            logger.info(f"[WebRecon] [domain={domain}] Results cached in {cache_time:.3f}s")
            
            if progress_callback:
                logger.info(f"[WebRecon] [domain={domain}] Calling progress_callback(100, 'Discovery complete')")
                progress_callback(100, "Discovery complete")
            
            total_time = time.time() - discovery_start
            logger.info(
                f"[WebRecon] [domain={domain}] Discovery completed in {total_time:.3f}s - "
                f"subdomains: {len(results['subdomains'])}, endpoints: {len(results['endpoints'])}, "
                f"files: {len(results['files'])}, source_code: {len(results['source_code'])}, "
                f"admin_panels: {len(results['admin_panels'])}, configs: {len(results['configs'])}"
            )
            
            return results
            
        except Exception as e:
            total_time = time.time() - discovery_start
            logger.error(
                f"[WebRecon] [domain={domain}] Discovery failed after {total_time:.3f}s: {e}",
                exc_info=True
            )
            raise
    
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
        """Enumerate subdomains with comprehensive wordlist.
        
        Args:
            domain: Target domain
            
        Returns:
            List of discovered subdomains
        """
        import time
        enum_start = time.time()
        logger.info(f"[WebRecon] [domain={domain}] Starting subdomain enumeration with wordlist")
        subdomains = []
        
        # Extended subdomain wordlist
        common_prefixes = [
            # Common
            'www', 'mail', 'email', 'webmail', 'smtp', 'pop', 'imap',
            'ftp', 'sftp', 'ssh', 'vpn', 'remote', 'secure',
            # Infrastructure
            'ns1', 'ns2', 'dns', 'mx', 'mx1', 'mx2',
            'server', 'servers', 'host', 'hosting',
            # Development
            'dev', 'development', 'staging', 'stage', 'test', 'testing',
            'qa', 'prod', 'production', 'preprod', 'pre-prod',
            # Services
            'api', 'api1', 'api2', 'apis', 'rest', 'graphql',
            'cdn', 'static', 'assets', 'media', 'files', 'download',
            'upload', 'storage', 'backup', 'backups',
            # Applications
            'app', 'apps', 'application', 'portal', 'dashboard',
            'admin', 'administrator', 'panel', 'cpanel', 'whm',
            'blog', 'blogs', 'forum', 'forums', 'wiki', 'docs',
            'documentation', 'help', 'support', 'status', 'monitor',
            # CI/CD
            'jenkins', 'gitlab', 'github', 'git', 'svn', 'hg',
            'ci', 'cd', 'deploy', 'deployment',
            # Other
            'mobile', 'm', 'wap', 'old', 'new', 'legacy',
            'shop', 'store', 'payment', 'pay', 'billing',
            'auth', 'login', 'signin', 'account', 'accounts',
        ]
        
        logger.info(f"[WebRecon] [domain={domain}] Checking {len(common_prefixes)} subdomain prefixes")
        
        # First, perform DNS resolution checks for all subdomains
        dns_start = time.time()
        dns_tasks = []
        subdomain_list = []
        for prefix in common_prefixes:
            subdomain = f"{prefix}.{domain}"
            
            # Skip if already seen
            if self._seen_urls.contains(subdomain):
                continue
            self._seen_urls.add(subdomain)
            
            subdomain_list.append(subdomain)
            dns_tasks.append(self._resolve_dns(subdomain))
        
        # Resolve all DNS queries in parallel
        dns_results = await asyncio.gather(*dns_tasks, return_exceptions=True)
        dns_time = time.time() - dns_start
        
        # Filter to only subdomains that resolved
        resolved_subdomains = []
        dns_failed = 0
        for subdomain, resolved in zip(subdomain_list, dns_results):
            if isinstance(resolved, Exception):
                logger.debug(f"[WebRecon] [domain={domain}] DNS resolution error for {subdomain}: {type(resolved).__name__}: {resolved}")
                dns_failed += 1
            elif resolved:
                resolved_subdomains.append(subdomain)
            else:
                logger.debug(f"[WebRecon] [domain={domain}] DNS resolution failed for {subdomain} (hostname not found)")
                dns_failed += 1
        
        logger.info(
            f"[WebRecon] [domain={domain}] DNS resolution completed in {dns_time:.3f}s - "
            f"resolved: {len(resolved_subdomains)}, failed: {dns_failed}"
        )
        
        tasks_created = 0
        tasks_skipped = 0
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            tasks = []
            for subdomain in resolved_subdomains:
                # Check both HTTPS and HTTP
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{subdomain}"
                    tasks.append(self._check_subdomain(client, url, subdomain, protocol == 'https'))
                    tasks_created += 1
            
            logger.info(
                f"[WebRecon] [domain={domain}] Created {tasks_created} subdomain check tasks "
                f"(skipped {tasks_skipped} duplicates, {dns_failed} DNS failures)"
            )
            
            # Run checks in parallel
            check_start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            check_time = time.time() - check_start
            logger.info(f"[WebRecon] [domain={domain}] Completed {len(results)} subdomain checks in {check_time:.3f}s")
            
            successful = 0
            errors = 0
            for result in results:
                if isinstance(result, Exception):
                    errors += 1
                    logger.warning(f"[WebRecon] [domain={domain}] Subdomain check error: {type(result).__name__}: {result}")
                elif isinstance(result, dict) and result:
                    successful += 1
                    # Avoid duplicates
                    existing = next((s for s in subdomains if s["subdomain"] == result["subdomain"]), None)
                    if not existing:
                        subdomains.append(result)
                        logger.info(f"[WebRecon] [domain={domain}] Found subdomain: {result.get('subdomain')} (status: {result.get('status')})")
                    elif result.get("https") and not existing.get("https"):
                        # Prefer HTTPS version
                        subdomains.remove(existing)
                        subdomains.append(result)
                        logger.info(f"[WebRecon] [domain={domain}] Upgraded subdomain to HTTPS: {result.get('subdomain')}")
            
            enum_time = time.time() - enum_start
            logger.info(
                f"[WebRecon] [domain={domain}] Subdomain enumeration completed in {enum_time:.3f}s - "
                f"found: {len(subdomains)}, successful: {successful}, errors: {errors}"
            )
        
        return subdomains
    
    async def _check_subdomain(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        subdomain: str, 
        is_https: bool
    ) -> Optional[Dict[str, Any]]:
        """Check if a subdomain is accessible."""
        import time
        request_start = time.time()
        protocol = "HTTPS" if is_https else "HTTP"
        logger.info(f"[WebRecon] [subdomain={subdomain}] Checking {protocol} GET {url}")
        
        try:
            response = await client.get(url, timeout=5.0)
            request_time = time.time() - request_start
            content_length = len(response.content) if response.content else 0
            server_header = response.headers.get("server", "unknown")
            
            result = {
                "subdomain": subdomain,
                "status": response.status_code,
                "https": is_https,
                "url": url,
                "server": server_header,
                "title": self._extract_title(response.text) if response.text else ""
            }
            logger.info(
                f"[WebRecon] [subdomain={subdomain}] HTTP {protocol} GET {url} - "
                f"Status: {response.status_code} - Time: {request_time:.3f}s - "
                f"Size: {content_length} bytes - Server: {server_header}"
            )
            return result
        except httpx.TimeoutException:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [subdomain={subdomain}] Timeout checking {url} after {request_time:.3f}s")
            return None
        except httpx.ConnectError as e:
            request_time = time.time() - request_start
            # Check if this is a DNS resolution error
            error_str = str(e).lower()
            is_dns_error = "name or service not known" in error_str or "errno -2" in error_str
            if is_dns_error:
                logger.debug(f"[WebRecon] [subdomain={subdomain}] DNS resolution error for {url} after {request_time:.3f}s: {type(e).__name__}: {e}")
            else:
                logger.warning(f"[WebRecon] [subdomain={subdomain}] Connection error for {url} after {request_time:.3f}s: {type(e).__name__}: {e}")
            return None
        except Exception as e:
            request_time = time.time() - request_start
            # Check if this is a DNS resolution error
            error_str = str(e).lower()
            is_dns_error = "name or service not known" in error_str or "errno -2" in error_str
            if is_dns_error:
                logger.debug(f"[WebRecon] [subdomain={subdomain}] DNS resolution error for {url} after {request_time:.3f}s: {type(e).__name__}: {e}")
            else:
                logger.warning(f"[WebRecon] [subdomain={subdomain}] Error checking {url} after {request_time:.3f}s: {type(e).__name__}: {e}")
            return None
    
    def _extract_title(self, html: str) -> str:
        """Extract page title from HTML."""
        try:
            match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:100]
        except:
            pass
        return ""
    
    async def _check_endpoints(self, domain: str) -> List[Dict[str, Any]]:
        """Check common endpoints.
        
        Args:
            domain: Target domain
            
        Returns:
            List of discovered endpoints
        """
        import time
        endpoint_start = time.time()
        logger.info(f"[WebRecon] [domain={domain}] Starting endpoint scanning")
        endpoints = []
        
        # Extended list of sensitive endpoints
        paths = [
            # Source control
            '/.git/config', '/.git/HEAD', '/.git/index',
            '/.svn/entries', '/.svn/wc.db',
            '/.hg/requires',
            # Environment and config
            '/.env', '/.env.local', '/.env.production',
            '/config.php', '/config.inc.php', '/configuration.php',
            '/web.config', '/.htaccess', '/.htpasswd',
            # Admin and login
            '/admin', '/administrator', '/wp-admin', '/wp-login.php',
            '/login', '/signin', '/auth', '/dashboard',
            '/phpmyadmin', '/pma', '/adminer.php',
            '/cpanel', '/whm', '/plesk',
            # API and docs
            '/api', '/api/v1', '/api/v2', '/graphql',
            '/swagger', '/swagger.json', '/swagger.yaml',
            '/openapi.json', '/openapi.yaml',
            '/docs', '/documentation', '/api-docs',
            # Debug and info
            '/phpinfo.php', '/info.php', '/test.php',
            '/server-status', '/server-info',
            '/.well-known/security.txt', '/security.txt',
            # Files and directories
            '/robots.txt', '/sitemap.xml', '/sitemap.txt',
            '/backup', '/backups', '/old', '/archive',
            '/dump', '/sql', '/database',
            # Other
            '/.DS_Store', '/Thumbs.db',
        ]
        
        logger.info(f"[WebRecon] [domain={domain}] Checking {len(paths)} endpoint paths")
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            tasks = []
            for path in paths:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}{path}"
                    if not self._seen_urls.contains(url):
                        self._seen_urls.add(url)
                        tasks.append(self._check_endpoint(client, url, path))
            
            logger.info(f"[WebRecon] [domain={domain}] Created {len(tasks)} endpoint check tasks")
            
            # Run checks in parallel with limit
            check_start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            check_time = time.time() - check_start
            logger.info(f"[WebRecon] [domain={domain}] Completed {len(results)} endpoint checks in {check_time:.3f}s")
            
            successful = 0
            errors = 0
            for result in results:
                if isinstance(result, Exception):
                    errors += 1
                    logger.warning(f"[WebRecon] [domain={domain}] Endpoint check error: {type(result).__name__}: {result}")
                elif isinstance(result, dict) and result:
                    successful += 1
                    endpoints.append(result)
                    logger.info(f"[WebRecon] [domain={domain}] Found endpoint: {result.get('path')} (status: {result.get('status')})")
            
            endpoint_time = time.time() - endpoint_start
            logger.info(
                f"[WebRecon] [domain={domain}] Endpoint scanning completed in {endpoint_time:.3f}s - "
                f"found: {len(endpoints)}, successful: {successful}, errors: {errors}"
            )
        
        return endpoints
    
    async def _check_endpoint(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        path: str
    ) -> Optional[Dict[str, Any]]:
        """Check a single endpoint."""
        import time
        request_start = time.time()
        protocol = "HTTPS" if url.startswith("https://") else "HTTP"
        
        try:
            response = await client.get(url, timeout=5.0)
            request_time = time.time() - request_start
            content_length = len(response.content) if response.content else 0
            content_type = response.headers.get("content-type", "unknown")
            server_header = response.headers.get("server", "unknown")
            
            if response.status_code != 404:
                result = {
                    "path": path,
                    "url": url,
                    "status": response.status_code,
                    "content_length": content_length,
                    "content_type": content_type,
                    "server": server_header
                }
                logger.info(
                    f"[WebRecon] [endpoint={path}] HTTP {protocol} GET {url} - "
                    f"Status: {response.status_code} - Time: {request_time:.3f}s - "
                    f"Size: {content_length} bytes - Type: {content_type} - Server: {server_header}"
                )
                return result
            else:
                logger.info(f"[WebRecon] [endpoint={path}] HTTP {protocol} GET {url} - Status: 404 (Not Found) - Time: {request_time:.3f}s")
        except httpx.TimeoutException:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [endpoint={path}] Timeout: {url} after {request_time:.3f}s")
        except httpx.ConnectError as e:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [endpoint={path}] Connection error: {url} after {request_time:.3f}s - {type(e).__name__}: {e}")
        except Exception as e:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [endpoint={path}] Error checking {url} after {request_time:.3f}s: {type(e).__name__}: {e}")
        return None
    
    async def _detect_sensitive_files(self, domain: str) -> List[Dict[str, Any]]:
        """Detect exposed sensitive files.
        
        Args:
            domain: Target domain
            
        Returns:
            List of detected sensitive files
        """
        import time
        file_start = time.time()
        logger.info(f"[WebRecon] [domain={domain}] Starting sensitive file detection")
        files = []
        
        # Sensitive file patterns
        sensitive_files = [
            # Environment files
            '/.env', '/.env.local', '/.env.production', '/.env.development',
            '/.env.test', '/.env.staging',
            # Configuration files
            '/config.json', '/config.yml', '/config.yaml',
            '/settings.json', '/settings.py', '/settings.php',
            '/application.properties', '/application.yml',
            # Key files
            '/id_rsa', '/id_dsa', '/id_ecdsa', '/id_ed25519',
            '/private.key', '/public.key', '/key.pem',
            '/certificate.pem', '/cert.pem',
            # Database files
            '/database.sql', '/dump.sql', '/backup.sql',
            '/db.sqlite', '/database.db',
            # Backup files
            '/backup.tar.gz', '/backup.zip', '/backup.rar',
            '/backup.bak', '/backup.old',
            # Log files
            '/error.log', '/access.log', '/debug.log',
            '/application.log', '/server.log',
            # Other sensitive
            '/.htpasswd', '/.gitignore', '/.dockerignore',
            '/composer.json', '/package.json', '/requirements.txt',
        ]
        
        logger.info(f"[WebRecon] [domain={domain}] Checking {len(sensitive_files)} sensitive file patterns")
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            tasks = []
            for file_path in sensitive_files:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}{file_path}"
                    if not self._seen_urls.contains(url):
                        self._seen_urls.add(url)
                        tasks.append(self._check_file(client, url, file_path))
            
            logger.info(f"[WebRecon] [domain={domain}] Created {len(tasks)} file check tasks")
            
            check_start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            check_time = time.time() - check_start
            logger.info(f"[WebRecon] [domain={domain}] Completed {len(results)} file checks in {check_time:.3f}s")
            
            successful = 0
            errors = 0
            for result in results:
                if isinstance(result, Exception):
                    errors += 1
                    logger.warning(f"[WebRecon] [domain={domain}] File check error: {type(result).__name__}: {result}")
                elif isinstance(result, dict) and result:
                    successful += 1
                    files.append(result)
                    logger.info(f"[WebRecon] [domain={domain}] Found sensitive file: {result.get('path')} ({result.get('content_length', 0)} bytes)")
            
            file_time = time.time() - file_start
            logger.info(
                f"[WebRecon] [domain={domain}] Sensitive file detection completed in {file_time:.3f}s - "
                f"found: {len(files)}, successful: {successful}, errors: {errors}"
            )
        
        return files
    
    async def _check_file(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Check if a sensitive file is accessible."""
        import time
        request_start = time.time()
        protocol = "HTTPS" if url.startswith("https://") else "HTTP"
        
        try:
            response = await client.get(url, timeout=5.0)
            request_time = time.time() - request_start
            content_length = len(response.content) if response.content else 0
            content_type = response.headers.get("content-type", "unknown")
            
            if response.status_code == 200:
                content_preview = response.text[:500] if response.text else ""
                result = {
                    "path": file_path,
                    "url": url,
                    "status": response.status_code,
                    "content_length": content_length,
                    "content_type": content_type,
                    "content_preview": content_preview,
                    "file_type": file_path.split('.')[-1] if '.' in file_path else "unknown"
                }
                logger.info(
                    f"[WebRecon] [file={file_path}] HTTP {protocol} GET {url} - "
                    f"Status: 200 (EXPOSED) - Time: {request_time:.3f}s - "
                    f"Size: {content_length} bytes - Type: {content_type}"
                )
                return result
            else:
                logger.info(f"[WebRecon] [file={file_path}] HTTP {protocol} GET {url} - Status: {response.status_code} - Time: {request_time:.3f}s")
        except httpx.TimeoutException:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [file={file_path}] Timeout: {url} after {request_time:.3f}s")
        except httpx.ConnectError as e:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [file={file_path}] Connection error: {url} after {request_time:.3f}s - {type(e).__name__}: {e}")
        except Exception as e:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [file={file_path}] Error checking {url} after {request_time:.3f}s: {type(e).__name__}: {e}")
        return None
    
    async def _detect_source_code_exposure(self, domain: str) -> List[Dict[str, Any]]:
        """Detect exposed source code repositories.
        
        Args:
            domain: Target domain
            
        Returns:
            List of source code exposures
        """
        import time
        exposure_start = time.time()
        logger.info(f"[WebRecon] [domain={domain}] Starting source code exposure detection")
        exposures = []
        
        # Source control indicators
        vcs_indicators = [
            # Git
            ('/.git/config', 'git'),
            ('/.git/HEAD', 'git'),
            ('/.git/index', 'git'),
            ('/.git/logs/HEAD', 'git'),
            # SVN
            ('/.svn/entries', 'svn'),
            ('/.svn/wc.db', 'svn'),
            # Mercurial
            ('/.hg/requires', 'hg'),
            ('/.hg/hgrc', 'hg'),
            # Other
            ('/.bzr/README', 'bzr'),
            ('/_darcs/README', 'darcs'),
        ]
        
        logger.info(f"[WebRecon] [domain={domain}] Checking {len(vcs_indicators)} VCS indicators")
        check_count = 0
        found_count = 0
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            for path, vcs_type in vcs_indicators:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}{path}"
                    if not self._seen_urls.contains(url):
                        self._seen_urls.add(url)
                        check_count += 1
                        request_start = time.time()
                        try:
                            response = await client.get(url, timeout=5.0)
                            request_time = time.time() - request_start
                            if response.status_code == 200:
                                content_length = len(response.content) if response.content else 0
                                found_count += 1
                                logger.info(
                                    f"[WebRecon] [vcs={vcs_type}] HTTP {protocol.upper()} GET {url} - "
                                    f"Status: 200 (EXPOSED) - Time: {request_time:.3f}s - "
                                    f"Size: {content_length} bytes - CRITICAL: VCS repository exposed"
                                )
                                exposures.append({
                                    "type": vcs_type,
                                    "path": path,
                                    "url": url,
                                    "status": response.status_code,
                                    "content_length": content_length,
                                    "severity": "critical"
                                })
                                break  # Found, no need to check http if https works
                            else:
                                logger.info(f"[WebRecon] [vcs={vcs_type}] HTTP {protocol.upper()} GET {url} - Status: {response.status_code} - Time: {request_time:.3f}s")
                        except httpx.TimeoutException:
                            request_time = time.time() - request_start
                            logger.warning(f"[WebRecon] [vcs={vcs_type}] Timeout checking {url} after {request_time:.3f}s")
                        except httpx.ConnectError as e:
                            request_time = time.time() - request_start
                            logger.warning(f"[WebRecon] [vcs={vcs_type}] Connection error checking {url} after {request_time:.3f}s: {type(e).__name__}: {e}")
                        except Exception as e:
                            request_time = time.time() - request_start
                            logger.warning(f"[WebRecon] [vcs={vcs_type}] Error checking {url} after {request_time:.3f}s: {type(e).__name__}: {e}")
        
        exposure_time = time.time() - exposure_start
        logger.info(
            f"[WebRecon] [domain={domain}] Source code exposure detection completed in {exposure_time:.3f}s - "
            f"checked: {check_count}, found: {found_count}"
        )
        return exposures
    
    async def _discover_admin_panels(self, domain: str) -> List[Dict[str, Any]]:
        """Discover admin panels and login pages.
        
        Args:
            domain: Target domain
            
        Returns:
            List of discovered admin panels
        """
        import time
        admin_start = time.time()
        logger.info(f"[WebRecon] [domain={domain}] Starting admin panel discovery")
        admin_panels = []
        
        # Common admin panel paths
        admin_paths = [
            # WordPress
            ('/wp-admin', 'WordPress Admin'),
            ('/wp-login.php', 'WordPress Login'),
            # Joomla
            ('/administrator', 'Joomla Admin'),
            # Drupal
            ('/user/login', 'Drupal Login'),
            # Generic
            ('/admin', 'Generic Admin'),
            ('/admin/login', 'Admin Login'),
            ('/administrator/login', 'Administrator Login'),
            ('/login', 'Login Page'),
            ('/signin', 'Sign In'),
            ('/dashboard', 'Dashboard'),
            # Database
            ('/phpmyadmin', 'phpMyAdmin'),
            ('/pma', 'phpMyAdmin (alt)'),
            ('/adminer.php', 'Adminer'),
            # Control panels
            ('/cpanel', 'cPanel'),
            ('/whm', 'WHM'),
            ('/plesk', 'Plesk'),
            # Other
            ('/manager', 'Tomcat Manager'),
            ('/jenkins', 'Jenkins'),
            ('/gitlab', 'GitLab'),
        ]
        
        logger.info(f"[WebRecon] [domain={domain}] Checking {len(admin_paths)} admin panel paths")
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            tasks = []
            for path, panel_name in admin_paths:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}{path}"
                    if not self._seen_urls.contains(url):
                        self._seen_urls.add(url)
                        tasks.append(self._check_admin_panel(client, url, path, panel_name))
            
            logger.info(f"[WebRecon] [domain={domain}] Created {len(tasks)} admin panel check tasks")
            check_start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            check_time = time.time() - check_start
            logger.info(f"[WebRecon] [domain={domain}] Completed {len(results)} admin panel checks in {check_time:.3f}s")
            
            successful = 0
            errors = 0
            for result in results:
                if isinstance(result, Exception):
                    errors += 1
                    logger.warning(f"[WebRecon] [domain={domain}] Admin panel check error: {type(result).__name__}: {result}")
                elif isinstance(result, dict) and result:
                    successful += 1
                    admin_panels.append(result)
        
        admin_time = time.time() - admin_start
        logger.info(
            f"[WebRecon] [domain={domain}] Admin panel discovery completed in {admin_time:.3f}s - "
            f"found: {len(admin_panels)}, successful: {successful}, errors: {errors}"
        )
        return admin_panels
    
    async def _check_admin_panel(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        path: str, 
        panel_name: str
    ) -> Optional[Dict[str, Any]]:
        """Check if an admin panel is accessible."""
        import time
        request_start = time.time()
        protocol = "HTTPS" if url.startswith("https://") else "HTTP"
        
        try:
            response = await client.get(url, timeout=5.0)
            request_time = time.time() - request_start
            content_length = len(response.content) if response.content else 0
            server_header = response.headers.get("server", "unknown")
            
            # Check for common indicators
            content_lower = response.text.lower() if response.text else ""
            is_login_page = any(keyword in content_lower for keyword in [
                'login', 'password', 'username', 'sign in', 'log in'
            ])
            
            if response.status_code in [200, 301, 302, 401, 403] or is_login_page:
                severity = "high" if response.status_code == 200 else "medium"
                logger.info(
                    f"[WebRecon] [admin_panel={panel_name}] HTTP {protocol} GET {url} - "
                    f"Status: {response.status_code} - Time: {request_time:.3f}s - "
                    f"Size: {content_length} bytes - Server: {server_header} - "
                    f"Login page: {is_login_page} - Severity: {severity}"
                )
                return {
                    "name": panel_name,
                    "path": path,
                    "url": url,
                    "status": response.status_code,
                    "is_login_page": is_login_page,
                    "severity": severity
                }
            else:
                logger.info(f"[WebRecon] [admin_panel={panel_name}] HTTP {protocol} GET {url} - Status: {response.status_code} - Time: {request_time:.3f}s")
        except httpx.TimeoutException:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [admin_panel={panel_name}] Timeout: {url} after {request_time:.3f}s")
        except httpx.ConnectError as e:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [admin_panel={panel_name}] Connection error: {url} after {request_time:.3f}s - {type(e).__name__}: {e}")
        except Exception as e:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [admin_panel={panel_name}] Error checking {url} after {request_time:.3f}s: {type(e).__name__}: {e}")
        return None
    
    async def _detect_config_files(self, domain: str) -> List[Dict[str, Any]]:
        """Detect exposed configuration files.
        
        Args:
            domain: Target domain
            
        Returns:
            List of detected configuration files
        """
        import time
        config_start = time.time()
        logger.info(f"[WebRecon] [domain={domain}] Starting configuration file detection")
        configs = []
        
        # Configuration file patterns
        config_files = [
            '/config.php', '/config.inc.php', '/configuration.php',
            '/config.json', '/config.yml', '/config.yaml',
            '/settings.php', '/settings.py', '/settings.json',
            '/application.properties', '/application.yml',
            '/application.yaml', '/application.conf',
            '/web.config', '/.htaccess', '/.htpasswd',
            '/.env', '/.env.production', '/.env.local',
        ]
        
        logger.info(f"[WebRecon] [domain={domain}] Checking {len(config_files)} configuration file patterns")
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            tasks = []
            for config_path in config_files:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}{config_path}"
                    if not self._seen_urls.contains(url):
                        self._seen_urls.add(url)
                        tasks.append(self._check_config_file(client, url, config_path))
            
            logger.info(f"[WebRecon] [domain={domain}] Created {len(tasks)} config file check tasks")
            check_start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            check_time = time.time() - check_start
            logger.info(f"[WebRecon] [domain={domain}] Completed {len(results)} config file checks in {check_time:.3f}s")
            
            successful = 0
            errors = 0
            for result in results:
                if isinstance(result, Exception):
                    errors += 1
                    logger.warning(f"[WebRecon] [domain={domain}] Config file check error: {type(result).__name__}: {result}")
                elif isinstance(result, dict) and result:
                    successful += 1
                    configs.append(result)
        
        config_time = time.time() - config_start
        logger.info(
            f"[WebRecon] [domain={domain}] Configuration file detection completed in {config_time:.3f}s - "
            f"found: {len(configs)}, successful: {successful}, errors: {errors}"
        )
        return configs
    
    async def _check_config_file(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        config_path: str
    ) -> Optional[Dict[str, Any]]:
        """Check if a configuration file is accessible."""
        import time
        request_start = time.time()
        protocol = "HTTPS" if url.startswith("https://") else "HTTP"
        
        try:
            response = await client.get(url, timeout=5.0)
            request_time = time.time() - request_start
            content_length = len(response.content) if response.content else 0
            content_type = response.headers.get("content-type", "unknown")
            
            if response.status_code == 200:
                # Check if it looks like a config file
                content = response.text if response.text else ""
                is_config = any(keyword in content.lower() for keyword in [
                    'password', 'secret', 'key', 'api', 'database', 'db_',
                    'host', 'port', 'user', 'config', 'setting'
                ])
                
                if is_config or config_path.endswith(('.env', '.config', '.conf')):
                    logger.info(
                        f"[WebRecon] [config={config_path}] HTTP {protocol} GET {url} - "
                        f"Status: 200 (EXPOSED) - Time: {request_time:.3f}s - "
                        f"Size: {content_length} bytes - Type: {content_type} - "
                        f"Contains secrets: {is_config}"
                    )
                    return {
                        "path": config_path,
                        "url": url,
                        "status": response.status_code,
                        "content_length": content_length,
                        "content_preview": content[:200],
                        "severity": "critical"
                    }
                else:
                    logger.info(f"[WebRecon] [config={config_path}] HTTP {protocol} GET {url} - Status: 200 - Time: {request_time:.3f}s (not a config file)")
            else:
                logger.info(f"[WebRecon] [config={config_path}] HTTP {protocol} GET {url} - Status: {response.status_code} - Time: {request_time:.3f}s")
        except httpx.TimeoutException:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [config={config_path}] Timeout: {url} after {request_time:.3f}s")
        except httpx.ConnectError as e:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [config={config_path}] Connection error: {url} after {request_time:.3f}s - {type(e).__name__}: {e}")
        except Exception as e:
            request_time = time.time() - request_start
            logger.warning(f"[WebRecon] [config={config_path}] Error checking {url} after {request_time:.3f}s: {type(e).__name__}: {e}")
        return None
    
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


