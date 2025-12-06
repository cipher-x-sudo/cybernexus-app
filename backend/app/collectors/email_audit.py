"""
Email Security Audit Collector

Inspired by: espoofer
Purpose: Analyze email security configurations (SPF, DKIM, DMARC).
"""

import asyncio
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
import dns.resolver
from loguru import logger

from app.core.dsa import HashMap, AVLTree, Graph


class EmailAudit:
    """
    Email Security Audit Collector.
    
    Features:
    - SPF record analysis
    - DKIM selector discovery
    - DMARC policy evaluation
    - Email spoofing risk assessment
    
    DSA Usage:
    - HashMap: DNS record caching
    - AVLTree: Domain index
    - Graph: Email infrastructure mapping
    """
    
    # Common DKIM selectors to check
    COMMON_DKIM_SELECTORS = [
        'default', 'google', 'selector1', 'selector2', 'k1', 'k2',
        's1', 's2', 'dkim', 'mail', 'email', 'smtp', 'mx',
        'mandrill', 'amazonses', 'sendgrid', 'mailchimp', 'postmark'
    ]
    
    def __init__(self):
        """Initialize Email Audit collector."""
        self._dns_cache = HashMap()
        self._domain_index = AVLTree()
        self._infra_graph = Graph(directed=True)
        self._resolver = dns.resolver.Resolver()
        self._resolver.timeout = 5
        self._resolver.lifetime = 5
    
    async def audit(self, domain: str) -> Dict[str, Any]:
        """Perform email security audit on domain.
        
        Args:
            domain: Target domain
            
        Returns:
            Audit results
        """
        logger.info(f"Starting email security audit for {domain}")
        
        results = {
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
            "spf": await self._check_spf(domain),
            "dkim": await self._check_dkim(domain),
            "dmarc": await self._check_dmarc(domain),
            "mx_records": await self._get_mx_records(domain),
            "risk_assessment": {},
            "score": 0
        }
        
        # Calculate risk assessment and score
        results["risk_assessment"] = self._assess_risk(results)
        results["score"] = self._calculate_score(results)
        
        # Add to infrastructure graph
        self._update_infra_graph(domain, results)
        
        # Index domain
        self._domain_index.insert(domain, results)
        
        return results
    
    async def _check_spf(self, domain: str) -> Dict[str, Any]:
        """Check SPF record.
        
        Args:
            domain: Target domain
            
        Returns:
            SPF analysis
        """
        result = {
            "exists": False,
            "record": None,
            "mechanisms": [],
            "all_mechanism": None,
            "includes": [],
            "issues": []
        }
        
        try:
            # Check cache first
            cache_key = f"spf:{domain}"
            cached = self._dns_cache.get(cache_key)
            if cached:
                return cached
            
            answers = self._resolver.resolve(domain, 'TXT')
            
            for rdata in answers:
                txt = rdata.to_text().strip('"')
                if txt.startswith('v=spf1'):
                    result["exists"] = True
                    result["record"] = txt
                    result["mechanisms"] = self._parse_spf(txt)
                    
                    # Extract 'all' mechanism
                    for mech in result["mechanisms"]:
                        if mech.endswith('all'):
                            result["all_mechanism"] = mech
                        if mech.startswith('include:'):
                            result["includes"].append(mech.replace('include:', ''))
                    
                    # Check for issues
                    if result["all_mechanism"] == '+all':
                        result["issues"].append({
                            "severity": "critical",
                            "issue": "SPF allows any sender (+all)"
                        })
                    elif result["all_mechanism"] is None:
                        result["issues"].append({
                            "severity": "high",
                            "issue": "No 'all' mechanism defined"
                        })
                    
                    if len(result["includes"]) > 10:
                        result["issues"].append({
                            "severity": "medium",
                            "issue": "Too many SPF includes (>10)"
                        })
                    
                    break
            
            # Cache result
            self._dns_cache.put(cache_key, result)
            
        except dns.resolver.NXDOMAIN:
            result["issues"].append({"severity": "info", "issue": "Domain does not exist"})
        except dns.resolver.NoAnswer:
            result["issues"].append({"severity": "high", "issue": "No SPF record found"})
        except Exception as e:
            result["issues"].append({"severity": "info", "issue": f"DNS error: {str(e)}"})
        
        return result
    
    def _parse_spf(self, record: str) -> List[str]:
        """Parse SPF record into mechanisms.
        
        Args:
            record: SPF record string
            
        Returns:
            List of mechanisms
        """
        # Remove 'v=spf1 ' prefix and split
        parts = record.replace('v=spf1 ', '').split()
        return parts
    
    async def _check_dkim(self, domain: str) -> Dict[str, Any]:
        """Check DKIM records.
        
        Args:
            domain: Target domain
            
        Returns:
            DKIM analysis
        """
        result = {
            "selectors_found": [],
            "selectors_checked": len(self.COMMON_DKIM_SELECTORS),
            "issues": []
        }
        
        for selector in self.COMMON_DKIM_SELECTORS:
            dkim_domain = f"{selector}._domainkey.{domain}"
            
            try:
                answers = self._resolver.resolve(dkim_domain, 'TXT')
                
                for rdata in answers:
                    txt = rdata.to_text().strip('"')
                    if 'v=DKIM1' in txt or 'p=' in txt:
                        selector_info = {
                            "selector": selector,
                            "record": txt,
                            "key_type": self._extract_dkim_key_type(txt)
                        }
                        result["selectors_found"].append(selector_info)
                        break
            
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                pass
            except Exception:
                pass
        
        if not result["selectors_found"]:
            result["issues"].append({
                "severity": "high",
                "issue": "No DKIM records found"
            })
        
        return result
    
    def _extract_dkim_key_type(self, record: str) -> Optional[str]:
        """Extract key type from DKIM record.
        
        Args:
            record: DKIM record string
            
        Returns:
            Key type or None
        """
        match = re.search(r'k=(\w+)', record)
        return match.group(1) if match else 'rsa'
    
    async def _check_dmarc(self, domain: str) -> Dict[str, Any]:
        """Check DMARC record.
        
        Args:
            domain: Target domain
            
        Returns:
            DMARC analysis
        """
        result = {
            "exists": False,
            "record": None,
            "policy": None,
            "subdomain_policy": None,
            "pct": 100,
            "rua": [],
            "ruf": [],
            "issues": []
        }
        
        dmarc_domain = f"_dmarc.{domain}"
        
        try:
            answers = self._resolver.resolve(dmarc_domain, 'TXT')
            
            for rdata in answers:
                txt = rdata.to_text().strip('"')
                if txt.startswith('v=DMARC1'):
                    result["exists"] = True
                    result["record"] = txt
                    
                    # Parse DMARC tags
                    tags = self._parse_dmarc(txt)
                    
                    result["policy"] = tags.get('p')
                    result["subdomain_policy"] = tags.get('sp', tags.get('p'))
                    result["pct"] = int(tags.get('pct', 100))
                    
                    if 'rua' in tags:
                        result["rua"] = tags['rua'].split(',')
                    if 'ruf' in tags:
                        result["ruf"] = tags['ruf'].split(',')
                    
                    # Check for issues
                    if result["policy"] == 'none':
                        result["issues"].append({
                            "severity": "high",
                            "issue": "DMARC policy is 'none' (monitoring only)"
                        })
                    
                    if result["pct"] < 100:
                        result["issues"].append({
                            "severity": "medium",
                            "issue": f"DMARC only applies to {result['pct']}% of emails"
                        })
                    
                    if not result["rua"]:
                        result["issues"].append({
                            "severity": "low",
                            "issue": "No aggregate report URI (rua) configured"
                        })
                    
                    break
        
        except dns.resolver.NXDOMAIN:
            result["issues"].append({"severity": "high", "issue": "No DMARC record found"})
        except dns.resolver.NoAnswer:
            result["issues"].append({"severity": "high", "issue": "No DMARC record found"})
        except Exception as e:
            result["issues"].append({"severity": "info", "issue": f"DNS error: {str(e)}"})
        
        return result
    
    def _parse_dmarc(self, record: str) -> Dict[str, str]:
        """Parse DMARC record into tags.
        
        Args:
            record: DMARC record string
            
        Returns:
            Dictionary of tags
        """
        tags = {}
        parts = record.split(';')
        
        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                tags[key.strip()] = value.strip()
        
        return tags
    
    async def _get_mx_records(self, domain: str) -> List[Dict[str, Any]]:
        """Get MX records for domain.
        
        Args:
            domain: Target domain
            
        Returns:
            List of MX records
        """
        mx_records = []
        
        try:
            answers = self._resolver.resolve(domain, 'MX')
            
            for rdata in answers:
                mx_records.append({
                    "priority": rdata.preference,
                    "exchange": str(rdata.exchange).rstrip('.')
                })
            
            mx_records.sort(key=lambda x: x['priority'])
        
        except Exception:
            pass
        
        return mx_records
    
    def _assess_risk(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess email spoofing risk.
        
        Args:
            results: Audit results
            
        Returns:
            Risk assessment
        """
        risk = {
            "spoofing_risk": "unknown",
            "factors": []
        }
        
        # Check SPF
        spf = results.get("spf", {})
        if not spf.get("exists"):
            risk["factors"].append("No SPF record - emails can be spoofed")
        elif spf.get("all_mechanism") == '+all':
            risk["factors"].append("SPF +all allows any sender")
        elif spf.get("all_mechanism") == '~all':
            risk["factors"].append("SPF softfail may allow spoofing")
        
        # Check DKIM
        dkim = results.get("dkim", {})
        if not dkim.get("selectors_found"):
            risk["factors"].append("No DKIM records - cannot verify email authenticity")
        
        # Check DMARC
        dmarc = results.get("dmarc", {})
        if not dmarc.get("exists"):
            risk["factors"].append("No DMARC - no policy enforcement")
        elif dmarc.get("policy") == 'none':
            risk["factors"].append("DMARC policy 'none' - monitoring only")
        
        # Calculate overall risk
        if len(risk["factors"]) >= 3:
            risk["spoofing_risk"] = "critical"
        elif len(risk["factors"]) >= 2:
            risk["spoofing_risk"] = "high"
        elif len(risk["factors"]) >= 1:
            risk["spoofing_risk"] = "medium"
        else:
            risk["spoofing_risk"] = "low"
        
        return risk
    
    def _calculate_score(self, results: Dict[str, Any]) -> int:
        """Calculate email security score.
        
        Args:
            results: Audit results
            
        Returns:
            Score 0-100
        """
        score = 0
        
        # SPF (max 30 points)
        spf = results.get("spf", {})
        if spf.get("exists"):
            score += 15
            if spf.get("all_mechanism") == '-all':
                score += 15
            elif spf.get("all_mechanism") == '~all':
                score += 10
            elif spf.get("all_mechanism") == '?all':
                score += 5
        
        # DKIM (max 30 points)
        dkim = results.get("dkim", {})
        if dkim.get("selectors_found"):
            score += 30
        
        # DMARC (max 40 points)
        dmarc = results.get("dmarc", {})
        if dmarc.get("exists"):
            score += 15
            if dmarc.get("policy") == 'reject':
                score += 25
            elif dmarc.get("policy") == 'quarantine':
                score += 15
            elif dmarc.get("policy") == 'none':
                score += 5
        
        return score
    
    def _update_infra_graph(self, domain: str, results: Dict[str, Any]):
        """Update infrastructure graph with audit results.
        
        Args:
            domain: Domain
            results: Audit results
        """
        # Add domain node
        self._infra_graph.add_node(domain, label=domain, node_type="domain")
        
        # Add MX servers
        for mx in results.get("mx_records", []):
            mx_domain = mx["exchange"]
            self._infra_graph.add_node(mx_domain, label=mx_domain, node_type="mx")
            self._infra_graph.add_edge(domain, mx_domain, relation="mx_record")
        
        # Add SPF includes
        for include in results.get("spf", {}).get("includes", []):
            self._infra_graph.add_node(include, label=include, node_type="spf_include")
            self._infra_graph.add_edge(domain, include, relation="spf_include")
    
    def get_domains_by_score(self, min_score: int = 0, max_score: int = 100) -> List[Dict[str, Any]]:
        """Get domains within score range.
        
        Args:
            min_score: Minimum score
            max_score: Maximum score
            
        Returns:
            List of domains with results
        """
        results = self._domain_index.range_query(min_score, max_score)
        return [{"domain": domain, "results": data} for domain, data in results]
    
    def stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        return {
            "domains_audited": len(self._domain_index),
            "dns_cache_size": len(self._dns_cache),
            "infrastructure_nodes": self._infra_graph.node_count,
            "infrastructure_edges": self._infra_graph.edge_count
        }


