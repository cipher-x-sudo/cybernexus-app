"""
Web Reconnaissance Collector

Inspired by: oxdork, lookyloo
Purpose: Asset discovery through dorking and domain analysis.
"""

import asyncio
import re
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
        logger.info(f"Starting comprehensive asset discovery for {domain}")
        
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
        
        if progress_callback:
            progress_callback(5, "Initializing discovery...")
        
        # Generate dorks for this domain
        dorks = self.generate_dorks(domain)
        results["dorks_generated"] = len(dorks)
        logger.info(f"Generated {len(dorks)} dork queries for {domain}")
        
        if progress_callback:
            progress_callback(10, "Enumerating subdomains...")
        
        # Discover subdomains
        subdomains = await self._enumerate_subdomains(domain)
        results["subdomains"] = subdomains
        logger.info(f"Discovered {len(subdomains)} subdomains")
        
        if progress_callback:
            progress_callback(30, "Scanning endpoints...")
        
        # Check common endpoints
        endpoints = await self._check_endpoints(domain)
        results["endpoints"] = endpoints
        logger.info(f"Discovered {len(endpoints)} endpoints")
        
        if progress_callback:
            progress_callback(50, "Detecting sensitive files...")
        
        # Deep file detection
        files = await self._detect_sensitive_files(domain)
        results["files"] = files
        logger.info(f"Detected {len(files)} sensitive files")
        
        if progress_callback:
            progress_callback(65, "Checking for source code exposure...")
        
        # Source code exposure detection
        source_code = await self._detect_source_code_exposure(domain)
        results["source_code"] = source_code
        logger.info(f"Found {len(source_code)} source code exposures")
        
        if progress_callback:
            progress_callback(75, "Scanning admin panels...")
        
        # Admin panel discovery
        admin_panels = await self._discover_admin_panels(domain)
        results["admin_panels"] = admin_panels
        logger.info(f"Discovered {len(admin_panels)} admin panels")
        
        if progress_callback:
            progress_callback(85, "Checking configuration files...")
        
        # Configuration file detection
        configs = await self._detect_config_files(domain)
        results["configs"] = configs
        logger.info(f"Found {len(configs)} configuration files")
        
        if progress_callback:
            progress_callback(95, "Finalizing results...")
        
        # Cache results
        self._asset_cache.put(domain, results)
        
        if progress_callback:
            progress_callback(100, "Discovery complete")
        
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
        """Enumerate subdomains with comprehensive wordlist.
        
        Args:
            domain: Target domain
            
        Returns:
            List of discovered subdomains
        """
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
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            tasks = []
            for prefix in common_prefixes:
                subdomain = f"{prefix}.{domain}"
                
                # Skip if already seen
                if self._seen_urls.contains(subdomain):
                    continue
                self._seen_urls.add(subdomain)
                
                # Check both HTTPS and HTTP
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{subdomain}"
                    tasks.append(self._check_subdomain(client, url, subdomain, protocol == 'https'))
            
            # Run checks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict) and result:
                    # Avoid duplicates
                    existing = next((s for s in subdomains if s["subdomain"] == result["subdomain"]), None)
                    if not existing:
                        subdomains.append(result)
                    elif result.get("https") and not existing.get("https"):
                        # Prefer HTTPS version
                        subdomains.remove(existing)
                        subdomains.append(result)
        
        return subdomains
    
    async def _check_subdomain(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        subdomain: str, 
        is_https: bool
    ) -> Optional[Dict[str, Any]]:
        """Check if a subdomain is accessible."""
        try:
            response = await client.get(url, timeout=5.0)
            return {
                "subdomain": subdomain,
                "status": response.status_code,
                "https": is_https,
                "url": url,
                "server": response.headers.get("server", ""),
                "title": self._extract_title(response.text) if response.text else ""
            }
        except:
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
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            tasks = []
            for path in paths:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}{path}"
                    if not self._seen_urls.contains(url):
                        self._seen_urls.add(url)
                        tasks.append(self._check_endpoint(client, url, path))
            
            # Run checks in parallel with limit
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict) and result:
                    endpoints.append(result)
        
        return endpoints
    
    async def _check_endpoint(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        path: str
    ) -> Optional[Dict[str, Any]]:
        """Check a single endpoint."""
        try:
            response = await client.get(url, timeout=5.0)
            if response.status_code != 404:
                return {
                    "path": path,
                    "url": url,
                    "status": response.status_code,
                    "content_length": len(response.content),
                    "content_type": response.headers.get("content-type", ""),
                    "server": response.headers.get("server", "")
                }
        except Exception as e:
            logger.debug(f"Error checking {url}: {e}")
        return None
    
    async def _detect_sensitive_files(self, domain: str) -> List[Dict[str, Any]]:
        """Detect exposed sensitive files.
        
        Args:
            domain: Target domain
            
        Returns:
            List of detected sensitive files
        """
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
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            tasks = []
            for file_path in sensitive_files:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}{file_path}"
                    if not self._seen_urls.contains(url):
                        self._seen_urls.add(url)
                        tasks.append(self._check_file(client, url, file_path))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict) and result:
                    files.append(result)
        
        return files
    
    async def _check_file(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Check if a sensitive file is accessible."""
        try:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                content_preview = response.text[:500] if response.text else ""
                return {
                    "path": file_path,
                    "url": url,
                    "status": response.status_code,
                    "content_length": len(response.content),
                    "content_type": response.headers.get("content-type", ""),
                    "content_preview": content_preview,
                    "file_type": file_path.split('.')[-1] if '.' in file_path else "unknown"
                }
        except Exception as e:
            logger.debug(f"Error checking file {url}: {e}")
        return None
    
    async def _detect_source_code_exposure(self, domain: str) -> List[Dict[str, Any]]:
        """Detect exposed source code repositories.
        
        Args:
            domain: Target domain
            
        Returns:
            List of source code exposures
        """
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
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            for path, vcs_type in vcs_indicators:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}{path}"
                    if not self._seen_urls.contains(url):
                        self._seen_urls.add(url)
                        try:
                            response = await client.get(url, timeout=5.0)
                            if response.status_code == 200:
                                exposures.append({
                                    "type": vcs_type,
                                    "path": path,
                                    "url": url,
                                    "status": response.status_code,
                                    "content_length": len(response.content),
                                    "severity": "critical"
                                })
                                break  # Found, no need to check http if https works
                        except:
                            pass
        
        return exposures
    
    async def _discover_admin_panels(self, domain: str) -> List[Dict[str, Any]]:
        """Discover admin panels and login pages.
        
        Args:
            domain: Target domain
            
        Returns:
            List of discovered admin panels
        """
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
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            tasks = []
            for path, panel_name in admin_paths:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}{path}"
                    if not self._seen_urls.contains(url):
                        self._seen_urls.add(url)
                        tasks.append(self._check_admin_panel(client, url, path, panel_name))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict) and result:
                    admin_panels.append(result)
        
        return admin_panels
    
    async def _check_admin_panel(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        path: str, 
        panel_name: str
    ) -> Optional[Dict[str, Any]]:
        """Check if an admin panel is accessible."""
        try:
            response = await client.get(url, timeout=5.0)
            # Check for common indicators
            content_lower = response.text.lower() if response.text else ""
            is_login_page = any(keyword in content_lower for keyword in [
                'login', 'password', 'username', 'sign in', 'log in'
            ])
            
            if response.status_code in [200, 301, 302, 401, 403] or is_login_page:
                return {
                    "name": panel_name,
                    "path": path,
                    "url": url,
                    "status": response.status_code,
                    "is_login_page": is_login_page,
                    "severity": "high" if response.status_code == 200 else "medium"
                }
        except Exception as e:
            logger.debug(f"Error checking admin panel {url}: {e}")
        return None
    
    async def _detect_config_files(self, domain: str) -> List[Dict[str, Any]]:
        """Detect exposed configuration files.
        
        Args:
            domain: Target domain
            
        Returns:
            List of detected configuration files
        """
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
        
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            tasks = []
            for config_path in config_files:
                for protocol in ['https', 'http']:
                    url = f"{protocol}://{domain}{config_path}"
                    if not self._seen_urls.contains(url):
                        self._seen_urls.add(url)
                        tasks.append(self._check_config_file(client, url, config_path))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict) and result:
                    configs.append(result)
        
        return configs
    
    async def _check_config_file(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        config_path: str
    ) -> Optional[Dict[str, Any]]:
        """Check if a configuration file is accessible."""
        try:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 200:
                # Check if it looks like a config file
                content = response.text if response.text else ""
                is_config = any(keyword in content.lower() for keyword in [
                    'password', 'secret', 'key', 'api', 'database', 'db_',
                    'host', 'port', 'user', 'config', 'setting'
                ])
                
                if is_config or config_path.endswith(('.env', '.config', '.conf')):
                    return {
                        "path": config_path,
                        "url": url,
                        "status": response.status_code,
                        "content_length": len(response.content),
                        "content_preview": content[:200],
                        "severity": "critical"
                    }
        except Exception as e:
            logger.debug(f"Error checking config file {url}: {e}")
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


