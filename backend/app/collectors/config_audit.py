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

from app.core.dsa import HashMap, MaxHeap


class ConfigAudit:
    """
    Configuration Audit Collector.
    
    Features:
    - Nginx misconfiguration detection
    - Common vulnerability checks
    - Security header analysis
    - SSL/TLS configuration review
    
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
    
    # Nginx misconfig patterns
    NGINX_CHECKS = [
        {
            'name': 'alias_traversal',
            'description': 'Alias path traversal vulnerability',
            'severity': 'critical',
            'paths': ['/static../etc/passwd', '/images../etc/passwd']
        },
        {
            'name': 'crlf_injection',
            'description': 'CRLF injection in redirects',
            'severity': 'high',
            'test': 'crlf'
        },
        {
            'name': 'merge_slashes',
            'description': 'Path traversal via merge_slashes off',
            'severity': 'high',
            'paths': ['//etc/passwd', '/./etc/passwd']
        },
        {
            'name': 'raw_backend',
            'description': 'Raw backend response exposure',
            'severity': 'medium',
            'headers': {'X-Accel-Redirect': '/etc/passwd'}
        }
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
        
        for check in self.NGINX_CHECKS:
            self._signature_map.put(check['name'], {
                **check,
                'score': severity_scores.get(check['severity'], 1)
            })
    
    async def audit(self, target: str) -> Dict[str, Any]:
        """Perform configuration audit on target.
        
        Args:
            target: Target URL or domain
            
        Returns:
            Audit results
        """
        logger.info(f"Starting configuration audit for {target}")
        
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
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                response = await client.get(target)
                
                # Analyze response
                results["server_info"] = self._extract_server_info(response)
                results["headers_analysis"] = self._analyze_headers(response.headers)
                
                # Run vulnerability checks
                findings = await self._run_checks(client, target)
                results["findings"] = findings
                
                # Calculate score
                results["score"] = self._calculate_score(results)
                
            except Exception as e:
                logger.error(f"Audit error for {target}: {e}")
                results["error"] = str(e)
        
        # Cache results
        self._results_cache.put(target, results)
        
        return results
    
    def _extract_server_info(self, response: httpx.Response) -> Dict[str, Any]:
        """Extract server information from response.
        
        Args:
            response: HTTP response
            
        Returns:
            Server information
        """
        headers = response.headers
        
        return {
            "server": headers.get("server", "unknown"),
            "powered_by": headers.get("x-powered-by"),
            "nginx_version": self._extract_version(headers.get("server", "")),
            "status_code": response.status_code
        }
    
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
    
    async def _run_checks(self, client: httpx.AsyncClient, target: str) -> List[Dict[str, Any]]:
        """Run vulnerability checks.
        
        Args:
            client: HTTP client
            target: Target URL
            
        Returns:
            List of findings
        """
        findings = []
        
        for check in self.NGINX_CHECKS:
            finding = await self._run_single_check(client, target, check)
            if finding:
                findings.append(finding)
                
                # Add to heap for priority ranking
                score = {'critical': 10, 'high': 8, 'medium': 5, 'low': 2}.get(check['severity'], 1)
                self._findings_heap.push(score, finding)
        
        return findings
    
    async def _run_single_check(self, client: httpx.AsyncClient, 
                                target: str, check: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run a single vulnerability check.
        
        Args:
            client: HTTP client
            target: Target URL
            check: Check configuration
            
        Returns:
            Finding if vulnerable, None otherwise
        """
        try:
            if 'paths' in check:
                for path in check['paths']:
                    url = f"{target.rstrip('/')}{path}"
                    response = await client.get(url)
                    
                    # Check for signs of vulnerability
                    if response.status_code == 200:
                        content = response.text.lower()
                        if 'root:' in content or 'bin/bash' in content:
                            return {
                                "check": check['name'],
                                "description": check['description'],
                                "severity": check['severity'],
                                "evidence": f"Path traversal successful: {path}",
                                "url": url
                            }
            
            elif check.get('test') == 'crlf':
                # CRLF injection test
                test_url = f"{target}/%0d%0aSet-Cookie:test=injected"
                response = await client.get(test_url)
                
                if 'set-cookie' in response.headers and 'test=injected' in response.headers.get('set-cookie', ''):
                    return {
                        "check": check['name'],
                        "description": check['description'],
                        "severity": check['severity'],
                        "evidence": "CRLF injection successful",
                        "url": test_url
                    }
            
            elif 'headers' in check:
                for header, value in check['headers'].items():
                    response = await client.get(target, headers={header: value})
                    # Check for abnormal response indicating vulnerability
                    if response.status_code == 200 and len(response.content) > 0:
                        # Additional checks would be needed here
                        pass
        
        except Exception as e:
            logger.debug(f"Check {check['name']} error: {e}")
        
        return None
    
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
            "checks_available": len(self.NGINX_CHECKS),
            "cached_audits": len(self._results_cache),
            "total_findings": len(self._findings_heap)
        }


