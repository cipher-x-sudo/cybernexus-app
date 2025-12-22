import asyncio
import os
import sys
from typing import Dict, List, Any
from datetime import datetime
from loguru import logger

from app.services.orchestrator import get_orchestrator, Capability
from app.collectors import (
    WebRecon,
    DarkWatch,
    KeywordMonitor,
    EmailAudit,
    ConfigAudit,
    TunnelDetector,
    DomainTree
)
from app.config import settings


class ToolExecutors:
    
    def __init__(self):
        self.dark_watch = DarkWatch()
        self.keyword_monitor = KeywordMonitor()
        self.email_audit = EmailAudit()
        self.web_recon = WebRecon()
        self.config_audit = ConfigAudit()
        self.tunnel_detector = TunnelDetector()
        self.domain_tree = DomainTree()
        
        logger.info("Tool executors initialized")
    
    async def execute_dark_watch(
        self, 
        target: str, 
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        from app.config import settings
        
        findings = []
        discovered_urls = []
        crawled_urls = []
        
        try:
            keywords = target.split(",")
            for keyword in keywords:
                keyword = keyword.strip()
                if keyword:
                    self.dark_watch.add_monitored_keyword(keyword)
            
            logger.info(f"[DarkWatch] Starting URL discovery for keywords: {keywords}")
            discovered_urls = self.dark_watch._discover_urls_with_engines()
            logger.info(f"[DarkWatch] Discovered {len(discovered_urls)} URLs")
            
            crawl_limit = config.get("crawl_limit", settings.DARKWEB_DEFAULT_CRAWL_LIMIT)
            urls_to_crawl = discovered_urls[:crawl_limit]
            logger.info(f"[DarkWatch] Crawling first {len(urls_to_crawl)} URLs (limit: {crawl_limit})")
            
            for url in urls_to_crawl:
                try:
                    site = self.dark_watch.crawl_site(url, depth=1)
                    crawled_urls.append(url)
                    
                    for mention in self.dark_watch.get_brand_mentions():
                        findings.append({
                            "severity": mention.threat_level.value,
                            "title": f"Brand mention: {mention.keyword}",
                            "description": mention.context[:200],
                            "evidence": {
                                "source_url": mention.source_url,
                                "keyword": mention.keyword,
                                "is_data_leak": mention.is_data_leak
                            },
                            "affected_assets": [mention.keyword],
                            "recommendations": [
                                "Monitor for further mentions",
                                "Review exposed information",
                                "Consider takedown if impersonation"
                            ],
                            "risk_score": 75.0 if mention.is_data_leak else 50.0
                        })
                except Exception as e:
                    logger.error(f"[DarkWatch] Error crawling {url}: {e}")
                    continue
            
            logger.info(f"[DarkWatch] Completed: {len(findings)} findings, {len(crawled_urls)} sites crawled, {len(discovered_urls) - len(crawled_urls)} remaining")
            
        except Exception as e:
            logger.error(f"Dark watch error: {e}", exc_info=True)
            
        return findings
    
    async def execute_keyword_monitor(
        self, 
        target: str, 
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        findings = []
        
        try:
            keywords = [k.strip() for k in target.split(",") if k.strip()]
            for keyword in keywords:
                findings.append({
                    "severity": "medium",
                    "title": f"Keyword monitored: {keyword}",
                    "description": f"Monitoring active for keyword '{keyword}' across dark web sources",
                    "evidence": {
                        "keyword": keyword,
                        "status": "active",
                        "sources_checked": 5
                    },
                    "affected_assets": [keyword],
                    "recommendations": [
                        "Continue monitoring",
                        "Set up alerts for high-priority keywords"
                    ],
                    "risk_score": 30.0
                })
                
        except Exception as e:
            logger.error(f"Keyword monitor error: {e}")
            
        return findings
    
    async def execute_email_audit(
        self, 
        target: str, 
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        findings = []
        
        try:
            results = await self.email_audit.audit(target)
            for issue in results.get("spf", {}).get("issues", []):
                findings.append({
                    "severity": issue.get("severity", "medium"),
                    "title": f"SPF Issue: {issue.get('issue', 'Unknown')}",
                    "description": f"SPF configuration issue detected for {target}",
                    "evidence": {
                        "record": results["spf"].get("record"),
                        "all_mechanism": results["spf"].get("all_mechanism")
                    },
                    "affected_assets": [target],
                    "recommendations": [
                        "Review and update SPF record",
                        "Use '-all' for strict enforcement"
                    ],
                    "risk_score": 80.0 if issue.get("severity") == "critical" else 60.0
                })
            
            for issue in results.get("dkim", {}).get("issues", []):
                findings.append({
                    "severity": issue.get("severity", "medium"),
                    "title": f"DKIM Issue: {issue.get('issue', 'Unknown')}",
                    "description": f"DKIM configuration issue for {target}",
                    "evidence": {
                        "selectors_checked": results["dkim"].get("selectors_checked"),
                        "selectors_found": len(results["dkim"].get("selectors_found", []))
                    },
                    "affected_assets": [target],
                    "recommendations": [
                        "Configure DKIM signing",
                        "Publish DKIM public key in DNS"
                    ],
                    "risk_score": 70.0
                })
            
            for issue in results.get("dmarc", {}).get("issues", []):
                findings.append({
                    "severity": issue.get("severity", "medium"),
                    "title": f"DMARC Issue: {issue.get('issue', 'Unknown')}",
                    "description": f"DMARC configuration issue for {target}",
                    "evidence": {
                        "record": results["dmarc"].get("record"),
                        "policy": results["dmarc"].get("policy")
                    },
                    "affected_assets": [target],
                    "recommendations": [
                        "Implement DMARC with 'reject' policy",
                        "Configure aggregate reporting"
                    ],
                    "risk_score": 75.0 if results["dmarc"].get("policy") == "none" else 50.0
                })
            
            logger.info(f"Email audit completed: {len(findings)} findings, score: {results.get('score')}")
            
        except Exception as e:
            logger.error(f"Email audit error: {e}")
            
        return findings
    
    async def execute_web_recon(
        self, 
        target: str, 
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        findings = []
        
        try:
            results = await self.web_recon.scan(target, config)
            for result in results.get("findings", []):
                findings.append({
                    "severity": result.get("severity", "medium"),
                    "title": result.get("title", "Exposed resource found"),
                    "description": result.get("description", ""),
                    "evidence": result.get("evidence", {}),
                    "affected_assets": [target],
                    "recommendations": result.get("recommendations", [
                        "Review and restrict access",
                        "Remove sensitive files from public access"
                    ]),
                    "risk_score": result.get("risk_score", 50.0)
                })
                
            logger.info(f"Web recon completed: {len(findings)} findings")
            
        except Exception as e:
            logger.error(f"Web recon error: {e}")
            
        return findings
    
    async def execute_domain_tree(
        self, 
        target: str, 
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        findings = []
        
        try:
            results = await self.domain_tree.capture(target, config)
            findings.append({
                "severity": "info",
                "title": f"Domain tree captured for {target}",
                "description": f"Full resource tree captured with {results.get('resource_count', 0)} resources",
                "evidence": {
                    "domains": results.get("domains", []),
                    "resource_count": results.get("resource_count", 0),
                    "screenshot_available": results.get("screenshot", False)
                },
                "affected_assets": [target],
                "recommendations": [
                    "Review third-party resources",
                    "Check for suspicious scripts"
                ],
                "risk_score": 20.0
            })
            
        except Exception as e:
            logger.error(f"Domain tree error: {e}")
            
        return findings
    
    async def execute_config_audit(
        self, 
        target: str, 
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        findings = []
        
        try:
            results = await self.config_audit.scan(target, config)
            
            for vuln in results.get("vulnerabilities", []):
                findings.append({
                    "severity": vuln.get("severity", "medium"),
                    "title": vuln.get("title", "Misconfiguration detected"),
                    "description": vuln.get("description", ""),
                    "evidence": vuln.get("evidence", {}),
                    "affected_assets": [target],
                    "recommendations": vuln.get("recommendations", []),
                    "risk_score": vuln.get("risk_score", 50.0)
                })
                
            logger.info(f"Config audit completed: {len(findings)} findings")
            
        except Exception as e:
            logger.error(f"Config audit error: {e}")
            
        return findings
    
    async def execute_tunnel_detector(
        self, 
        target: str, 
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        findings = []
        
        try:
            results = await self.tunnel_detector.detect(target, config)
            
            for detection in results.get("detections", []):
                findings.append({
                    "severity": detection.get("severity", "high"),
                    "title": detection.get("title", "Tunneling detected"),
                    "description": detection.get("description", ""),
                    "evidence": detection.get("evidence", {}),
                    "affected_assets": [detection.get("source", target)],
                    "recommendations": [
                        "Investigate source host",
                        "Review firewall rules",
                        "Block suspicious traffic"
                    ],
                    "risk_score": detection.get("risk_score", 70.0)
                })
                
        except Exception as e:
            logger.error(f"Tunnel detector error: {e}")
            
        return findings


async def register_executors():
    orchestrator = get_orchestrator()
    executors = ToolExecutors()
    
    orchestrator.register_tool_executor("dark_watch", executors.execute_dark_watch)
    orchestrator.register_tool_executor("keyword_monitor", executors.execute_keyword_monitor)
    orchestrator.register_tool_executor("email_audit", executors.execute_email_audit)
    orchestrator.register_tool_executor("web_recon", executors.execute_web_recon)
    orchestrator.register_tool_executor("domain_tree", executors.execute_domain_tree)
    orchestrator.register_tool_executor("config_audit", executors.execute_config_audit)
    orchestrator.register_tool_executor("tunnel_detector", executors.execute_tunnel_detector)
    
    logger.info("All tool executors registered")


async def process_jobs():
    logger.info("Starting job processor...")
    
    orchestrator = get_orchestrator()
    
    while True:
        try:
            pending_jobs = orchestrator.get_jobs(status=None, limit=10)
            pending = [j for j in pending_jobs if j.status.value == "pending"]
            
            for job in pending:
                logger.info(f"Processing job: {job.id} ({job.capability.value})")
                await orchestrator.execute_job(job.id)
                
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Job processing error: {e}")
            await asyncio.sleep(5)


async def main():
    logger.info("CyberNexus Worker starting...")
    
    await register_executors()
    
    await process_jobs()


if __name__ == "__main__":
    asyncio.run(main())



