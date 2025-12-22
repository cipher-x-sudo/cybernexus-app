import asyncio
import re
import json
import httpx
from typing import Any, Dict, List, Optional
from datetime import datetime
import dns.resolver
import dns.reversename
from loguru import logger

from app.core.dsa import HashMap, AVLTree, Graph


class EmailAudit:
    
    COMMON_DKIM_SELECTORS = [
        'default', 'google', 'selector1', 'selector2', 'k1', 'k2',
        's1', 's2', 'dkim', 'mail', 'email', 'smtp', 'mx',
        'mandrill', 'amazonses', 'sendgrid', 'mailchimp', 'postmark'
    ]
    
    def __init__(self):
        self._dns_cache = HashMap()
        self._domain_index = AVLTree()
        self._infra_graph = Graph(directed=True)
        self._resolver = dns.resolver.Resolver()
        self._resolver.timeout = 5
        self._resolver.lifetime = 5
    
    async def audit(self, domain: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        config = config or {}
        logger.info(f"Starting comprehensive email security audit for {domain}")
        
        checks = await asyncio.gather(
            self._check_spf(domain),
            self._check_dkim(domain),
            self._check_dmarc(domain),
            self._get_mx_records(domain),
            return_exceptions=True
        )
        
        spf, dkim, dmarc, mx_records = checks
        
        if isinstance(spf, Exception):
            logger.error(f"SPF check failed: {spf}")
            spf = {"exists": False, "issues": [{"severity": "info", "issue": f"Error: {str(spf)}"}]}
        if isinstance(dkim, Exception):
            logger.error(f"DKIM check failed: {dkim}")
            dkim = {"selectors_found": [], "issues": [{"severity": "info", "issue": f"Error: {str(dkim)}"}]}
        if isinstance(dmarc, Exception):
            logger.error(f"DMARC check failed: {dmarc}")
            dmarc = {"exists": False, "issues": [{"severity": "info", "issue": f"Error: {str(dmarc)}"}]}
        if isinstance(mx_records, Exception):
            logger.error(f"MX records check failed: {mx_records}")
            mx_records = []
        
        results = {
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
            "spf": spf,
            "dkim": dkim,
            "dmarc": dmarc,
            "mx_records": mx_records,
            "risk_assessment": {},
            "score": 0
        }
        
        if config.get("check_bimi", True):
            results["bimi"] = await self._check_bimi(domain)
        
        if config.get("check_mta_sts", True):
            results["mta_sts"] = await self._check_mta_sts(domain)
        
        if config.get("check_dane", True):
            results["dane"] = await self._check_dane(domain, mx_records)
        
        if config.get("check_arc", True):
            results["arc"] = await self._check_arc(domain)
        
        if config.get("check_ptr", True):
            results["ptr_records"] = await self._check_ptr_records(domain, mx_records)
        
        if config.get("check_dnssec", True):
            results["dnssec"] = await self._check_dnssec(domain)
        
        if config.get("check_subdomains", True):
            results["subdomains"] = await self._check_subdomains(domain)
        
        results["risk_assessment"] = self._assess_risk(results)
        results["score"] = self._calculate_score(results)
        results["compliance"] = self._calculate_compliance(results)
        
        self._update_infra_graph(domain, results)
        
        self._domain_index.insert(domain, results)
        
        return results
    
    async def _check_spf(self, domain: str) -> Dict[str, Any]:
        result = {
            "exists": False,
            "record": None,
            "mechanisms": [],
            "all_mechanism": None,
            "includes": [],
            "issues": []
        }
        
        try:
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
                    
                    for mech in result["mechanisms"]:
                        if mech.endswith('all'):
                            result["all_mechanism"] = mech
                        if mech.startswith('include:'):
                            result["includes"].append(mech.replace('include:', ''))
                    
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
            
            self._dns_cache.put(cache_key, result)
            
        except dns.resolver.NXDOMAIN:
            result["issues"].append({"severity": "info", "issue": "Domain does not exist"})
        except dns.resolver.NoAnswer:
            result["issues"].append({"severity": "high", "issue": "No SPF record found"})
        except Exception as e:
            result["issues"].append({"severity": "info", "issue": f"DNS error: {str(e)}"})
        
        return result
    
    def _parse_spf(self, record: str) -> List[str]:
        parts = record.replace('v=spf1 ', '').split()
        return parts
    
    async def _check_dkim(self, domain: str) -> Dict[str, Any]:
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
        match = re.search(r'k=(\w+)', record)
        return match.group(1) if match else 'rsa'
    
    async def _check_dmarc(self, domain: str) -> Dict[str, Any]:
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
                    
                    tags = self._parse_dmarc(txt)
                    
                    result["policy"] = tags.get('p')
                    result["subdomain_policy"] = tags.get('sp', tags.get('p'))
                    result["pct"] = int(tags.get('pct', 100))
                    
                    if 'rua' in tags:
                        result["rua"] = tags['rua'].split(',')
                    if 'ruf' in tags:
                        result["ruf"] = tags['ruf'].split(',')
                    
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
        tags = {}
        parts = record.split(';')
        
        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                tags[key.strip()] = value.strip()
        
        return tags
    
    async def _get_mx_records(self, domain: str) -> List[Dict[str, Any]]:
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
    
    async def _check_bimi(self, domain: str) -> Dict[str, Any]:
        result = {
            "exists": False,
            "record": None,
            "selector": "default",
            "v": None,
            "l": None,
            "a": None,
            "issues": []
        }
        
        try:
            bimi_domain = f"default._bimi.{domain}"
            answers = self._resolver.resolve(bimi_domain, 'TXT')
            
            for rdata in answers:
                txt = rdata.to_text().strip('"')
                if txt.startswith('v=BIMI1') or 'v=BIMI1' in txt:
                    result["exists"] = True
                    result["record"] = txt
                    
                    tags = self._parse_bimi(txt)
                    result["v"] = tags.get('v')
                    result["l"] = tags.get('l')
                    result["a"] = tags.get('a')
                    
                    if not result["l"]:
                        result["issues"].append({
                            "severity": "medium",
                            "issue": "BIMI record missing logo location (l=)"
                        })
                    
                    break
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            result["issues"].append({
                "severity": "low",
                "issue": "No BIMI record found (optional but recommended for brand protection)"
            })
        except Exception as e:
            result["issues"].append({
                "severity": "info",
                "issue": f"DNS error checking BIMI: {str(e)}"
            })
        
        return result
    
    def _parse_bimi(self, record: str) -> Dict[str, str]:
        tags = {}
        parts = record.split(';')
        
        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                tags[key.strip()] = value.strip()
        
        return tags
    
    async def _check_mta_sts(self, domain: str) -> Dict[str, Any]:
        result = {
            "exists": False,
            "dns_record": None,
            "policy_exists": False,
            "policy_url": None,
            "policy_content": None,
            "mode": None,
            "max_age": None,
            "issues": []
        }
        
        try:
            mta_sts_domain = f"_mta-sts.{domain}"
            answers = self._resolver.resolve(mta_sts_domain, 'TXT')
            
            for rdata in answers:
                txt = rdata.to_text().strip('"')
                if 'mta-sts' in txt.lower():
                    result["exists"] = True
                    result["dns_record"] = txt
                    
                    if 'v=STSv1' in txt:
                        policy_url = f"https://mta-sts.{domain}/.well-known/mta-sts.txt"
                        result["policy_url"] = policy_url
                        
                        try:
                            async with httpx.AsyncClient(timeout=5.0) as client:
                                response = await client.get(policy_url)
                                if response.status_code == 200:
                                    result["policy_exists"] = True
                                    result["policy_content"] = response.text
                                    
                                    for line in response.text.split('\n'):
                                        line = line.strip()
                                        if line.startswith('mode:'):
                                            result["mode"] = line.split(':', 1)[1].strip()
                                        elif line.startswith('max_age:'):
                                            result["max_age"] = line.split(':', 1)[1].strip()
                                    
                                    if result["mode"] == "none":
                                        result["issues"].append({
                                            "severity": "medium",
                                            "issue": "MTA-STS mode is 'none' (testing only)"
                                        })
                                    elif result["mode"] != "enforce":
                                        result["issues"].append({
                                            "severity": "low",
                                            "issue": f"MTA-STS mode is '{result['mode']}' (should be 'enforce')"
                                        })
                        except Exception as e:
                            result["issues"].append({
                                "severity": "medium",
                                "issue": f"Could not fetch MTA-STS policy: {str(e)}"
                            })
                    
                    break
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            result["issues"].append({
                "severity": "low",
                "issue": "No MTA-STS DNS record found (optional but recommended for secure email transport)"
            })
        except Exception as e:
            result["issues"].append({
                "severity": "info",
                "issue": f"DNS error checking MTA-STS: {str(e)}"
            })
        
        return result
    
    async def _check_dane(self, domain: str, mx_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        result = {
            "exists": False,
            "records": [],
            "issues": []
        }
        
        if not mx_records:
            result["issues"].append({
                "severity": "info",
                "issue": "No MX records to check DANE for"
            })
            return result
        
        for mx in mx_records[:3]:
            mx_host = mx.get("exchange", "")
            if not mx_host:
                continue
            
            try:
                tlsa_domain = f"_25._tcp.{mx_host}"
                answers = self._resolver.resolve(tlsa_domain, 'TLSA')
                
                for rdata in answers:
                    result["exists"] = True
                    result["records"].append({
                        "mx": mx_host,
                        "usage": rdata.usage,
                        "selector": rdata.selector,
                        "matching_type": rdata.matching_type,
                        "certificate": str(rdata.certificate_assoc_data)[:50] + "..."
                    })
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                pass
            except Exception:
                pass
        
        if not result["exists"]:
            result["issues"].append({
                "severity": "low",
                "issue": "No DANE TLSA records found (optional but recommended for certificate pinning)"
            })
        
        return result
    
    async def _check_arc(self, domain: str) -> Dict[str, Any]:
        result = {
            "configured": False,
            "note": "ARC is typically configured on mail servers, not DNS",
            "issues": []
        }
        
        result["note"] = "ARC authentication is handled by mail servers during message transit. Ensure SPF, DKIM, and DMARC are properly configured."
        
        return result
    
    async def _check_ptr_records(self, domain: str, mx_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        result = {
            "mx_servers": [],
            "issues": []
        }
        
        if not mx_records:
            return result
        
        for mx in mx_records[:3]:
            mx_host = mx.get("exchange", "")
            if not mx_host:
                continue
            
            mx_info = {
                "host": mx_host,
                "ptr_exists": False,
                "ptr_record": None,
                "reverse_matches": False
            }
            
            try:
                ip_answers = self._resolver.resolve(mx_host, 'A')
                for ip_rdata in ip_answers:
                    ip = str(ip_rdata)
                    
                    try:
                        ptr_answers = self._resolver.resolve(dns.reversename.from_address(ip), 'PTR')
                        for ptr_rdata in ptr_answers:
                            mx_info["ptr_exists"] = True
                            mx_info["ptr_record"] = str(ptr_rdata).rstrip('.')
                            
                            if domain in mx_info["ptr_record"] or mx_host in mx_info["ptr_record"]:
                                mx_info["reverse_matches"] = True
                    except Exception:
                        pass
                    
                    break
                
                if not mx_info["ptr_exists"]:
                    result["issues"].append({
                        "severity": "medium",
                        "issue": f"No PTR record for {mx_host} (may affect email deliverability)"
                    })
                elif not mx_info["reverse_matches"]:
                    result["issues"].append({
                        "severity": "low",
                        "issue": f"PTR record for {mx_host} doesn't match forward DNS"
                    })
                
            except Exception:
                pass
            
            result["mx_servers"].append(mx_info)
        
        return result
    
    async def _check_dnssec(self, domain: str) -> Dict[str, Any]:
        result = {
            "signed": False,
            "ds_record": None,
            "issues": []
        }
        
        try:
            answers = self._resolver.resolve(domain, 'DNSKEY')
            
            if answers:
                result["signed"] = True
            else:
                result["issues"].append({
                    "severity": "low",
                    "issue": "DNSSEC not detected (optional but recommended for DNS security)"
                })
        except Exception:
            result["issues"].append({
                "severity": "info",
                "issue": "Could not verify DNSSEC status"
            })
        
        return result
    
    async def _check_subdomains(self, domain: str) -> Dict[str, Any]:
        result = {
            "subdomains_checked": [],
            "subdomains_with_email_config": [],
            "issues": []
        }
        
        common_subdomains = [
            "mail", "email", "smtp", "mx", "imap", "pop", "webmail",
            "exchange", "owa", "autodiscover"
        ]
        
        for subdomain in common_subdomains:
            subdomain_full = f"{subdomain}.{domain}"
            
            subdomain_result = {
                "subdomain": subdomain_full,
                "has_mx": False,
                "has_spf": False,
                "has_dmarc": False,
                "has_dkim": False
            }
            
            try:
                try:
                    mx_answers = self._resolver.resolve(subdomain_full, 'MX')
                    if mx_answers:
                        subdomain_result["has_mx"] = True
                except:
                    pass
                
                try:
                    txt_answers = self._resolver.resolve(subdomain_full, 'TXT')
                    for rdata in txt_answers:
                        txt = rdata.to_text().strip('"')
                        if txt.startswith('v=spf1'):
                            subdomain_result["has_spf"] = True
                            break
                except:
                    pass
                
                try:
                    dmarc_domain = f"_dmarc.{subdomain_full}"
                    dmarc_answers = self._resolver.resolve(dmarc_domain, 'TXT')
                    for rdata in dmarc_answers:
                        txt = rdata.to_text().strip('"')
                        if txt.startswith('v=DMARC1'):
                            subdomain_result["has_dmarc"] = True
                            break
                except:
                    pass
                
                if any([subdomain_result["has_mx"], subdomain_result["has_spf"], 
                       subdomain_result["has_dmarc"], subdomain_result["has_dkim"]]):
                    result["subdomains_with_email_config"].append(subdomain_result)
                
            except Exception:
                pass
            
            result["subdomains_checked"].append(subdomain_result)
        
        for sub in result["subdomains_with_email_config"]:
            if sub["has_mx"] and not sub["has_spf"]:
                result["issues"].append({
                    "severity": "medium",
                    "issue": f"Subdomain {sub['subdomain']} has MX but no SPF record"
                })
            if sub["has_mx"] and not sub["has_dmarc"]:
                result["issues"].append({
                    "severity": "low",
                    "issue": f"Subdomain {sub['subdomain']} has MX but no DMARC record"
                })
        
        return result
    
    def _assess_risk(self, results: Dict[str, Any]) -> Dict[str, Any]:
        risk = {
            "spoofing_risk": "unknown",
            "factors": []
        }
        
        spf = results.get("spf", {})
        if not spf.get("exists"):
            risk["factors"].append("No SPF record - emails can be spoofed")
        elif spf.get("all_mechanism") == '+all':
            risk["factors"].append("SPF +all allows any sender")
        elif spf.get("all_mechanism") == '~all':
            risk["factors"].append("SPF softfail may allow spoofing")
        
        dkim = results.get("dkim", {})
        if not dkim.get("selectors_found"):
            risk["factors"].append("No DKIM records - cannot verify email authenticity")
        
        dmarc = results.get("dmarc", {})
        if not dmarc.get("exists"):
            risk["factors"].append("No DMARC - no policy enforcement")
        elif dmarc.get("policy") == 'none':
            risk["factors"].append("DMARC policy 'none' - monitoring only")
        
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
        score = 0
        
        spf = results.get("spf", {})
        if spf.get("exists"):
            score += 15
            if spf.get("all_mechanism") == '-all':
                score += 15
            elif spf.get("all_mechanism") == '~all':
                score += 10
            elif spf.get("all_mechanism") == '?all':
                score += 5
        
        dkim = results.get("dkim", {})
        if dkim.get("selectors_found"):
            score += 30
        
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
    
    def _calculate_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        compliance = {
            "rfc_7208_spf": {"compliant": False, "score": 0, "issues": []},
            "rfc_6376_dkim": {"compliant": False, "score": 0, "issues": []},
            "rfc_7489_dmarc": {"compliant": False, "score": 0, "issues": []},
            "m3aawg": {"compliant": False, "score": 0, "issues": []},
            "overall_score": 0
        }
        
        spf = results.get("spf", {})
        if spf.get("exists"):
            compliance["rfc_7208_spf"]["compliant"] = True
            compliance["rfc_7208_spf"]["score"] = 80
            
            if spf.get("all_mechanism") == '-all':
                compliance["rfc_7208_spf"]["score"] = 100
            elif spf.get("all_mechanism") == '~all':
                compliance["rfc_7208_spf"]["score"] = 70
            elif spf.get("all_mechanism") == '+all':
                compliance["rfc_7208_spf"]["score"] = 0
                compliance["rfc_7208_spf"]["issues"].append("SPF uses +all (allows all)")
            
            if len(spf.get("includes", [])) > 10:
                compliance["rfc_7208_spf"]["score"] -= 10
                compliance["rfc_7208_spf"]["issues"].append("Too many SPF includes (>10)")
        else:
            compliance["rfc_7208_spf"]["issues"].append("No SPF record found")
        
        dkim = results.get("dkim", {})
        if dkim.get("selectors_found"):
            compliance["rfc_6376_dkim"]["compliant"] = True
            compliance["rfc_6376_dkim"]["score"] = 100
        else:
            compliance["rfc_6376_dkim"]["issues"].append("No DKIM records found")
        
        dmarc = results.get("dmarc", {})
        if dmarc.get("exists"):
            compliance["rfc_7489_dmarc"]["compliant"] = True
            compliance["rfc_7489_dmarc"]["score"] = 60
            
            policy = dmarc.get("policy")
            if policy == 'reject':
                compliance["rfc_7489_dmarc"]["score"] = 100
            elif policy == 'quarantine':
                compliance["rfc_7489_dmarc"]["score"] = 80
            elif policy == 'none':
                compliance["rfc_7489_dmarc"]["score"] = 40
                compliance["rfc_7489_dmarc"]["issues"].append("DMARC policy is 'none'")
            
            if not dmarc.get("rua"):
                compliance["rfc_7489_dmarc"]["score"] -= 10
                compliance["rfc_7489_dmarc"]["issues"].append("No aggregate report URI")
            
            if dmarc.get("pct", 100) < 100:
                compliance["rfc_7489_dmarc"]["score"] -= 5
                compliance["rfc_7489_dmarc"]["issues"].append(f"DMARC only applies to {dmarc.get('pct')}% of emails")
        else:
            compliance["rfc_7489_dmarc"]["issues"].append("No DMARC record found")
        
        m3aawg_score = 0
        m3aawg_issues = []
        
        if spf.get("exists") and spf.get("all_mechanism") == '-all':
            m3aawg_score += 25
        else:
            m3aawg_issues.append("SPF should use -all")
        
        if dkim.get("selectors_found"):
            m3aawg_score += 25
        else:
            m3aawg_issues.append("DKIM should be configured")
        
        if dmarc.get("exists") and dmarc.get("policy") in ['quarantine', 'reject']:
            m3aawg_score += 25
        else:
            m3aawg_issues.append("DMARC should be set to quarantine or reject")
        
        if dmarc.get("exists") and dmarc.get("rua"):
            m3aawg_score += 25
        else:
            m3aawg_issues.append("DMARC should include aggregate reporting")
        
        compliance["m3aawg"]["score"] = m3aawg_score
        compliance["m3aawg"]["compliant"] = m3aawg_score >= 75
        compliance["m3aawg"]["issues"] = m3aawg_issues
        
        compliance["overall_score"] = (
            compliance["rfc_7208_spf"]["score"] * 0.3 +
            compliance["rfc_6376_dkim"]["score"] * 0.3 +
            compliance["rfc_7489_dmarc"]["score"] * 0.3 +
            compliance["m3aawg"]["score"] * 0.1
        )
        
        return compliance
    
    def _update_infra_graph(self, domain: str, results: Dict[str, Any]):
        self._infra_graph.add_node(domain, label=domain, node_type="domain")
        
        for mx in results.get("mx_records", []):
            mx_domain = mx["exchange"]
            self._infra_graph.add_node(mx_domain, label=mx_domain, node_type="mx")
            self._infra_graph.add_edge(domain, mx_domain, relation="mx_record")
        
        for include in results.get("spf", {}).get("includes", []):
            self._infra_graph.add_node(include, label=include, node_type="spf_include")
            self._infra_graph.add_edge(domain, include, relation="spf_include")
    
    def get_domains_by_score(self, min_score: int = 0, max_score: int = 100) -> List[Dict[str, Any]]:
        results = self._domain_index.range_query(min_score, max_score)
        return [{"domain": domain, "results": data} for domain, data in results]
    
    def stats(self) -> Dict[str, Any]:
        return {
            "domains_audited": len(self._domain_index),
            "dns_cache_size": len(self._dns_cache),
            "infrastructure_nodes": self._infra_graph.node_count,
            "infrastructure_edges": self._infra_graph.edge_count
        }


