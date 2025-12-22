from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import re
from urllib.parse import urlparse, urljoin
import json


import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dsa.graph import Graph
from core.dsa.hashmap import HashMap
from core.dsa.trie import Trie
from core.dsa.linked_list import DoublyLinkedList


class ResourceType(Enum):
    DOCUMENT = "document"
    SCRIPT = "script"
    STYLESHEET = "stylesheet"
    IMAGE = "image"
    FONT = "font"
    XHR = "xhr"
    FETCH = "fetch"
    WEBSOCKET = "websocket"
    MEDIA = "media"
    OTHER = "other"


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


@dataclass
class CapturedRequest:
    request_id: str
    url: str
    method: RequestMethod
    resource_type: ResourceType
    initiator: Optional[str]
    timestamp: datetime
    response_status: int = 0
    response_size: int = 0
    response_time_ms: float = 0
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: List[str] = field(default_factory=list)
    is_third_party: bool = False
    redirect_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "url": self.url,
            "method": self.method.value,
            "resource_type": self.resource_type.value,
            "initiator": self.initiator,
            "timestamp": self.timestamp.isoformat(),
            "response_status": self.response_status,
            "response_size": self.response_size,
            "response_time_ms": self.response_time_ms,
            "is_third_party": self.is_third_party,
            "redirect_url": self.redirect_url,
            "cookies_count": len(self.cookies)
        }


@dataclass
class DomainNode:
    domain: str
    full_url: str
    depth: int
    parent_domain: Optional[str]
    resource_type: ResourceType
    is_root: bool = False
    children: List[str] = field(default_factory=list)
    requests: List[str] = field(default_factory=list)
    cookies: Set[str] = field(default_factory=set)
    trackers_detected: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "domain": self.domain,
            "full_url": self.full_url,
            "depth": self.depth,
            "parent_domain": self.parent_domain,
            "resource_type": self.resource_type.value,
            "is_root": self.is_root,
            "children_count": len(self.children),
            "requests_count": len(self.requests),
            "cookies_count": len(self.cookies),
            "trackers": self.trackers_detected,
            "risk_score": self.risk_score
        }


@dataclass
class CaptureResult:
    capture_id: str
    target_url: str
    final_url: str
    captured_at: datetime
    capture_duration_ms: float
    domain_tree: Dict[str, DomainNode]
    requests: List[CapturedRequest]
    redirect_chain: List[str]
    unique_domains: Set[str]
    third_party_domains: Set[str]
    trackers: Dict[str, List[str]]
    cookies: Dict[str, List[str]]
    total_size_bytes: int
    risk_assessment: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "capture_id": self.capture_id,
            "target_url": self.target_url,
            "final_url": self.final_url,
            "captured_at": self.captured_at.isoformat(),
            "capture_duration_ms": self.capture_duration_ms,
            "domain_count": len(self.unique_domains),
            "third_party_count": len(self.third_party_domains),
            "request_count": len(self.requests),
            "redirect_count": len(self.redirect_chain),
            "tracker_count": sum(len(v) for v in self.trackers.values()),
            "cookie_count": sum(len(v) for v in self.cookies.values()),
            "total_size_bytes": self.total_size_bytes,
            "risk_assessment": self.risk_assessment
        }


class DomainTree:
    
    KNOWN_TRACKERS = [
        "google-analytics.com",
        "googletagmanager.com",
        "doubleclick.net",
        "facebook.net",
        "facebook.com/tr",
        "analytics.twitter.com",
        "ads.linkedin.com",
        "pixel.quantserve.com",
        "scorecardresearch.com",
        "amazon-adsystem.com",
        "criteo.com",
        "hotjar.com",
        "mixpanel.com",
        "segment.com",
        "optimizely.com",
        "newrelic.com",
        "sentry.io",
    ]
    
    CDN_DOMAINS = [
        "cloudflare.com",
        "cloudfront.net",
        "akamaized.net",
        "fastly.net",
        "jsdelivr.net",
        "unpkg.com",
        "cdnjs.cloudflare.com",
        "googleapis.com",
        "gstatic.com",
    ]
    
    def __init__(self):
        self.domain_graph = Graph(directed=True)
        
        self.captures = HashMap()
        self.domain_cache = HashMap()
        self.request_cache = HashMap()
        
        self.tracker_trie = Trie()
        self._build_tracker_trie()
        
        self.request_timeline = DoublyLinkedList()
        
        self.stats = {
            "total_captures": 0,
            "total_domains_analyzed": 0,
            "total_trackers_found": 0,
            "total_third_parties": 0,
        }
    
    def _build_tracker_trie(self):
        for tracker in self.KNOWN_TRACKERS:
            reversed_domain = '.'.join(reversed(tracker.split('.')))
            self.tracker_trie.insert(reversed_domain)
    
    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    def _get_base_domain(self, domain: str) -> str:
        parts = domain.split('.')
        if len(parts) >= 2:
            if parts[-1] in ['com', 'org', 'net', 'io', 'co', 'edu', 'gov']:
                if len(parts) >= 2:
                    return '.'.join(parts[-2:])
            if len(parts) >= 3 and parts[-2] in ['co', 'com', 'org', 'net']:
                return '.'.join(parts[-3:])
        return domain
    
    def _is_tracker(self, domain: str) -> Tuple[bool, Optional[str]]:
        reversed_domain = '.'.join(reversed(domain.split('.')))
        
        for tracker in self.KNOWN_TRACKERS:
            reversed_tracker = '.'.join(reversed(tracker.split('.')))
            if reversed_domain.startswith(reversed_tracker):
                return True, tracker
        
        return False, None
    
    def _is_cdn(self, domain: str) -> bool:
        base = self._get_base_domain(domain)
        return any(cdn in domain for cdn in self.CDN_DOMAINS)
    
    def _generate_capture_id(self, url: str) -> str:
        timestamp = datetime.now().isoformat()
        data = f"{url}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _generate_request_id(self, url: str, method: str) -> str:
        timestamp = datetime.now().isoformat()
        data = f"{method}:{url}:{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def _extract_requests_from_har(self, har: Dict[str, Any]) -> List[Dict[str, Any]]:
        requests = []
        entries = har.get('entries', [])
        
        for entry in entries:
            har_request = entry.get('request', {})
            har_response = entry.get('response', {})
            har_timings = entry.get('timings', {})
            
            url = har_request.get('url', '')
            method = har_request.get('method', 'GET')
            
            mime_type = har_response.get('content', {}).get('mimeType', '')
            resource_type = self._determine_resource_type(url, mime_type)
            
            total_time = sum(
                v for v in har_timings.values() 
                if isinstance(v, (int, float)) and v > 0
            )
            
            body_size = har_response.get('bodySize', 0)
            if body_size < 0:
                body_size = har_response.get('content', {}).get('size', 0)
            
            initiator = None
            headers = har_request.get('headers', [])
            for header in headers:
                if header.get('name', '').lower() == 'referer':
                    initiator = header.get('value')
                    break
            
            requests.append({
                "url": url,
                "method": method,
                "type": resource_type,
                "status": har_response.get('status', 0),
                "size": body_size,
                "time": total_time,
                "initiator": initiator,
                "mime_type": mime_type
            })
        
        return requests
    
    def _determine_resource_type(self, url: str, mime_type: str) -> str:
        url_lower = url.lower()
        mime_lower = mime_type.lower()
        
        if 'text/html' in mime_lower:
            return 'document'
        elif 'text/css' in mime_lower:
            return 'stylesheet'
        elif 'javascript' in mime_lower or 'application/javascript' in mime_lower:
            return 'script'
        elif 'image/' in mime_lower:
            return 'image'
        elif 'font' in mime_lower or 'woff' in mime_lower:
            return 'font'
        elif 'video' in mime_lower or 'audio' in mime_lower:
            return 'media'
        
        if url_lower.endswith(('.html', '.htm')):
            return 'document'
        elif url_lower.endswith('.css'):
            return 'stylesheet'
        elif url_lower.endswith(('.js', '.mjs')):
            return 'script'
        elif url_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')):
            return 'image'
        elif url_lower.endswith(('.woff', '.woff2', '.ttf', '.otf')):
            return 'font'
        elif url_lower.endswith(('.mp4', '.webm', '.mp3')):
            return 'media'
        
        return 'other'
    
    def _simulate_page_capture(self, url: str) -> List[Dict[str, Any]]:
        domain = self._extract_domain(url)
        base_domain = self._get_base_domain(domain)
        
        simulated_requests = [
            {
                "url": url,
                "method": "GET",
                "type": "document",
                "status": 200,
                "size": 45000,
                "time": 150,
                "initiator": None,
            },
            {
                "url": f"https://{domain}/assets/main.css",
                "method": "GET",
                "type": "stylesheet",
                "status": 200,
                "size": 12000,
                "time": 50,
                "initiator": url,
            },
            {
                "url": f"https://{domain}/assets/app.js",
                "method": "GET",
                "type": "script",
                "status": 200,
                "size": 85000,
                "time": 120,
                "initiator": url,
            },
            {
                "url": f"https://cdn.{base_domain}/images/logo.png",
                "method": "GET",
                "type": "image",
                "status": 200,
                "size": 5000,
                "time": 30,
                "initiator": url,
            },
            {
                "url": "https://www.google-analytics.com/analytics.js",
                "method": "GET",
                "type": "script",
                "status": 200,
                "size": 45000,
                "time": 80,
                "initiator": f"https://{domain}/assets/app.js",
            },
            {
                "url": "https://www.googletagmanager.com/gtm.js?id=GTM-XXXXX",
                "method": "GET",
                "type": "script",
                "status": 200,
                "size": 120000,
                "time": 95,
                "initiator": url,
            },
            {
                "url": "https://fonts.googleapis.com/css2?family=Roboto",
                "method": "GET",
                "type": "stylesheet",
                "status": 200,
                "size": 2000,
                "time": 40,
                "initiator": f"https://{domain}/assets/main.css",
            },
            {
                "url": "https://fonts.gstatic.com/s/roboto/v30/regular.woff2",
                "method": "GET",
                "type": "font",
                "status": 200,
                "size": 18000,
                "time": 60,
                "initiator": "https://fonts.googleapis.com/css2?family=Roboto",
            },
            {
                "url": "https://securepubads.g.doubleclick.net/tag/js/gpt.js",
                "method": "GET",
                "type": "script",
                "status": 200,
                "size": 95000,
                "time": 110,
                "initiator": url,
            },
            {
                "url": f"https://api.{base_domain}/v1/user/session",
                "method": "GET",
                "type": "xhr",
                "status": 200,
                "size": 500,
                "time": 25,
                "initiator": f"https://{domain}/assets/app.js",
            },
            {
                "url": "https://connect.facebook.net/en_US/fbevents.js",
                "method": "GET",
                "type": "script",
                "status": 200,
                "size": 55000,
                "time": 85,
                "initiator": f"https://{domain}/assets/app.js",
            },
        ]
        
        return simulated_requests
    
    async def capture_url_async(
        self,
        url: str,
        har_data: Optional[Dict[str, Any]] = None,
        follow_redirects: bool = True
    ) -> CaptureResult:
        start_time = datetime.now()
        capture_id = self._generate_capture_id(url)
        
        target_domain = self._extract_domain(url)
        target_base = self._get_base_domain(target_domain)
        
        if har_data:
            raw_requests = self._extract_requests_from_har(har_data)
        else:
            raw_requests = self._simulate_page_capture(url)
        
        return self._process_capture_requests(
            capture_id, url, target_domain, target_base,
            raw_requests, start_time, follow_redirects
        )
    
    def _process_capture_requests(
        self,
        capture_id: str,
        url: str,
        target_domain: str,
        target_base: str,
        raw_requests: List[Dict[str, Any]],
        start_time: datetime,
        follow_redirects: bool
    ) -> CaptureResult:
        captured_requests: List[CapturedRequest] = []
        domain_nodes: Dict[str, DomainNode] = {}
        unique_domains: Set[str] = set()
        third_party_domains: Set[str] = set()
        trackers: Dict[str, List[str]] = {}
        cookies: Dict[str, List[str]] = {}
        redirect_chain: List[str] = [url]
        total_size = 0
        
        root_node = DomainNode(
            domain=target_domain,
            full_url=url,
            depth=0,
            parent_domain=None,
            resource_type=ResourceType.DOCUMENT,
            is_root=True
        )
        domain_nodes[target_domain] = root_node
        unique_domains.add(target_domain)
        
        self.domain_graph.add_node(target_domain, label=target_domain, node_type="domain", data={"type": "root", "url": url})
        
        for req_data in raw_requests:
            req_url = req_data["url"]
            req_domain = self._extract_domain(req_url)
            req_base = self._get_base_domain(req_domain)
            

            request_id = self._generate_request_id(req_url, req_data["method"])
            
            resource_type = ResourceType(req_data["type"])
            
            is_third_party = req_base != target_base
            
            captured_req = CapturedRequest(
                request_id=request_id,
                url=req_url,
                method=RequestMethod(req_data["method"]),
                resource_type=resource_type,
                initiator=req_data.get("initiator"),
                timestamp=datetime.now(),
                response_status=req_data["status"],
                response_size=req_data["size"],
                response_time_ms=req_data["time"],
                is_third_party=is_third_party
            )
            captured_requests.append(captured_req)
            

            self.request_timeline.append(captured_req.to_dict())
            
            self.request_cache.put(request_id, captured_req)
            
            total_size += req_data["size"]
            unique_domains.add(req_domain)
            
            if is_third_party:
                third_party_domains.add(req_domain)
            
            is_tracker, tracker_name = self._is_tracker(req_domain)
            if is_tracker:
                if tracker_name not in trackers:
                    trackers[tracker_name] = []
                trackers[tracker_name].append(req_url)
            
            if req_domain not in domain_nodes:

                parent_domain = None
                depth = 1
                if req_data.get("initiator"):
                    initiator_domain = self._extract_domain(req_data["initiator"])
                    if initiator_domain in domain_nodes:
                        parent_domain = initiator_domain
                        depth = domain_nodes[initiator_domain].depth + 1
                        domain_nodes[initiator_domain].children.append(req_domain)
                
                node = DomainNode(
                    domain=req_domain,
                    full_url=req_url,
                    depth=depth,
                    parent_domain=parent_domain,
                    resource_type=resource_type
                )
                
                if is_tracker:
                    node.trackers_detected.append(tracker_name)
                    node.risk_score = 0.7
                elif is_third_party and not self._is_cdn(req_domain):
                    node.risk_score = 0.4
                
                domain_nodes[req_domain] = node
                
                self.domain_graph.add_node(
                    req_domain,
                    label=req_domain,
                    node_type="domain",
                    data={
                        "type": "third_party" if is_third_party else "first_party",
                        "is_tracker": is_tracker,
                        "resource_type": resource_type.value
                    }
                )
                
                if parent_domain:
                    self.domain_graph.add_edge(parent_domain, req_domain, weight=1.0)
            
            domain_nodes[req_domain].requests.append(request_id)
        
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        risk_assessment = self._assess_risk(
            third_party_count=len(third_party_domains),
            tracker_count=len(trackers),
            total_domains=len(unique_domains),
            redirect_count=len(redirect_chain) - 1
        )
        

        result = CaptureResult(
            capture_id=capture_id,
            target_url=url,
            final_url=url,
            captured_at=start_time,
            capture_duration_ms=duration_ms,
            domain_tree=domain_nodes,
            requests=captured_requests,
            redirect_chain=redirect_chain,
            unique_domains=unique_domains,
            third_party_domains=third_party_domains,
            trackers=trackers,
            cookies=cookies,
            total_size_bytes=total_size,
            risk_assessment=risk_assessment
        )
        
        self.captures.put(capture_id, result)
        

        self.stats["total_captures"] += 1
        self.stats["total_domains_analyzed"] += len(unique_domains)
        self.stats["total_trackers_found"] += len(trackers)
        self.stats["total_third_parties"] += len(third_party_domains)
        
        return result
    
    def capture_url(self, url: str, follow_redirects: bool = True) -> CaptureResult:
        start_time = datetime.now()
        capture_id = self._generate_capture_id(url)
        
        target_domain = self._extract_domain(url)
        target_base = self._get_base_domain(target_domain)
        
        raw_requests = self._simulate_page_capture(url)
        
        return self._process_capture_requests(
            capture_id, url, target_domain, target_base,
            raw_requests, start_time, follow_redirects
        )
        
        captured_requests: List[CapturedRequest] = []
        domain_nodes: Dict[str, DomainNode] = {}
        unique_domains: Set[str] = set()
        third_party_domains: Set[str] = set()
        trackers: Dict[str, List[str]] = {}
        cookies: Dict[str, List[str]] = {}
        redirect_chain: List[str] = [url]
        total_size = 0
        
        root_node = DomainNode(
            domain=target_domain,
            full_url=url,
            depth=0,
            parent_domain=None,
            resource_type=ResourceType.DOCUMENT,
            is_root=True
        )
        domain_nodes[target_domain] = root_node
        unique_domains.add(target_domain)
        
        self.domain_graph.add_node(target_domain, label=target_domain, node_type="domain", data={"type": "root", "url": url})
        
        for req_data in raw_requests:
            req_url = req_data["url"]
            req_domain = self._extract_domain(req_url)
            req_base = self._get_base_domain(req_domain)
            

            request_id = self._generate_request_id(req_url, req_data["method"])
            
            resource_type = ResourceType(req_data["type"])
            
            is_third_party = req_base != target_base
            
            captured_req = CapturedRequest(
                request_id=request_id,
                url=req_url,
                method=RequestMethod(req_data["method"]),
                resource_type=resource_type,
                initiator=req_data.get("initiator"),
                timestamp=datetime.now(),
                response_status=req_data["status"],
                response_size=req_data["size"],
                response_time_ms=req_data["time"],
                is_third_party=is_third_party
            )
            captured_requests.append(captured_req)
            

            self.request_timeline.append(captured_req.to_dict())
            
            self.request_cache.put(request_id, captured_req)
            
            total_size += req_data["size"]
            unique_domains.add(req_domain)
            
            if is_third_party:
                third_party_domains.add(req_domain)
            
            is_tracker, tracker_name = self._is_tracker(req_domain)
            if is_tracker:
                if tracker_name not in trackers:
                    trackers[tracker_name] = []
                trackers[tracker_name].append(req_url)
            
            if req_domain not in domain_nodes:

                parent_domain = None
                depth = 1
                if req_data.get("initiator"):
                    initiator_domain = self._extract_domain(req_data["initiator"])
                    if initiator_domain in domain_nodes:
                        parent_domain = initiator_domain
                        depth = domain_nodes[initiator_domain].depth + 1
                        domain_nodes[initiator_domain].children.append(req_domain)
                
                node = DomainNode(
                    domain=req_domain,
                    full_url=req_url,
                    depth=depth,
                    parent_domain=parent_domain,
                    resource_type=resource_type
                )
                
                if is_tracker:
                    node.trackers_detected.append(tracker_name)
                    node.risk_score = 0.7
                elif is_third_party and not self._is_cdn(req_domain):
                    node.risk_score = 0.4
                
                domain_nodes[req_domain] = node
                
                self.domain_graph.add_node(
                    req_domain,
                    label=req_domain,
                    node_type="domain",
                    data={
                        "type": "third_party" if is_third_party else "first_party",
                        "is_tracker": is_tracker,
                        "resource_type": resource_type.value
                    }
                )
                
                if parent_domain:
                    self.domain_graph.add_edge(parent_domain, req_domain, weight=1.0)
            
            domain_nodes[req_domain].requests.append(request_id)
        
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        risk_assessment = self._assess_risk(
            third_party_count=len(third_party_domains),
            tracker_count=len(trackers),
            total_domains=len(unique_domains),
            redirect_count=len(redirect_chain) - 1
        )
        

        result = CaptureResult(
            capture_id=capture_id,
            target_url=url,
            final_url=url,
            captured_at=start_time,
            capture_duration_ms=duration_ms,
            domain_tree=domain_nodes,
            requests=captured_requests,
            redirect_chain=redirect_chain,
            unique_domains=unique_domains,
            third_party_domains=third_party_domains,
            trackers=trackers,
            cookies=cookies,
            total_size_bytes=total_size,
            risk_assessment=risk_assessment
        )
        
        self.captures.put(capture_id, result)
        

        self.stats["total_captures"] += 1
        self.stats["total_domains_analyzed"] += len(unique_domains)
        self.stats["total_trackers_found"] += len(trackers)
        self.stats["total_third_parties"] += len(third_party_domains)
        
        return result
    
    def _assess_risk(
        self,
        third_party_count: int,
        tracker_count: int,
        total_domains: int,
        redirect_count: int
    ) -> Dict[str, Any]:
        score = 0
        factors = []
        
        if third_party_count > 20:
            score += 30
            factors.append("Excessive third-party domains (>20)")
        elif third_party_count > 10:
            score += 20
            factors.append("High third-party count (>10)")
        elif third_party_count > 5:
            score += 10
            factors.append("Moderate third-party count (>5)")
        
        if tracker_count > 5:
            score += 40
            factors.append("Many trackers detected (>5)")
        elif tracker_count > 2:
            score += 25
            factors.append("Multiple trackers detected (>2)")
        elif tracker_count > 0:
            score += 10
            factors.append("Trackers present")
        

        if redirect_count > 3:
            score += 15
            factors.append("Excessive redirects (>3)")
        elif redirect_count > 1:
            score += 8
            factors.append("Multiple redirects")
        
        if total_domains > 30:
            score += 15
            factors.append("Very complex domain structure (>30)")
        elif total_domains > 15:
            score += 8
            factors.append("Complex domain structure (>15)")
        
        if score >= 70:
            level = "critical"
        elif score >= 50:
            level = "high"
        elif score >= 30:
            level = "medium"
        else:
            level = "low"
        
        return {
            "score": min(score, 100),
            "level": level,
            "factors": factors,
            "third_party_count": third_party_count,
            "tracker_count": tracker_count,
            "total_domains": total_domains,
            "redirect_count": redirect_count
        }
    
    def get_domain_tree(self, capture_id: str) -> Optional[Dict]:
        result = self.captures.get(capture_id)
        if result:
            return {
                domain: node.to_dict()
                for domain, node in result.domain_tree.items()
            }
        return None
    
    def get_capture_graph(self, capture_id: str) -> Dict[str, Any]:
        result = self.captures.get(capture_id)
        if not result:
            return {"nodes": [], "edges": []}
        
        nodes = []
        edges = []
        
        for domain, node in result.domain_tree.items():
            is_tracker, _ = self._is_tracker(domain)
            
            nodes.append({
                "id": domain,
                "label": domain,
                "type": "root" if node.is_root else ("tracker" if is_tracker else "domain"),
                "depth": node.depth,
                "requests": len(node.requests),
                "risk": node.risk_score,
                "resource_type": node.resource_type.value
            })
            
            if node.parent_domain:
                edges.append({
                    "source": node.parent_domain,
                    "target": domain,
                    "type": node.resource_type.value
                })
        
        return {"nodes": nodes, "edges": edges}
    
    def compare_captures(
        self,
        capture_id_1: str,
        capture_id_2: str
    ) -> Dict[str, Any]:
        result1 = self.captures.get(capture_id_1)
        result2 = self.captures.get(capture_id_2)
        
        if not result1 or not result2:
            return {"error": "Capture not found"}
        
        domains1 = result1.unique_domains
        domains2 = result2.unique_domains
        
        return {
            "capture_1": capture_id_1,
            "capture_2": capture_id_2,
            "added_domains": list(domains2 - domains1),
            "removed_domains": list(domains1 - domains2),
            "common_domains": list(domains1 & domains2),
            "third_party_change": len(result2.third_party_domains) - len(result1.third_party_domains),
            "tracker_change": len(result2.trackers) - len(result1.trackers),
            "size_change": result2.total_size_bytes - result1.total_size_bytes,
            "risk_change": result2.risk_assessment["score"] - result1.risk_assessment["score"]
        }
    
    def find_tracker_connections(self) -> Dict[str, List[str]]:
        tracker_usage: Dict[str, List[str]] = {}
        
        for capture_id in self.captures.keys():
            result = self.captures.get(capture_id)
            if result:
                for tracker_domain in result.trackers.keys():
                    if tracker_domain not in tracker_usage:
                        tracker_usage[tracker_domain] = []
                    tracker_usage[tracker_domain].append(result.target_url)
        
        return tracker_usage
    
    def get_statistics(self) -> Dict[str, Any]:
        
        return {
            **self.stats,
            "graph_vertices": self.domain_graph.vertex_count(),
            "graph_edges": self.domain_graph.edge_count(),
            "cached_requests": self.request_cache.size(),
            "timeline_length": self.request_timeline.size
        }
    
    def export_capture(self, capture_id: str, format: str = "json") -> Optional[str]:
        result = self.captures.get(capture_id)
        if not result:
            return None
        
        if format == "json":
            export_data = {
                "capture": result.to_dict(),
                "domain_tree": {d: n.to_dict() for d, n in result.domain_tree.items()},
                "requests": [r.to_dict() for r in result.requests],
                "graph": self.get_capture_graph(capture_id)
            }
            return json.dumps(export_data, indent=2)
        
        elif format == "html":
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Domain Tree Report - {result.target_url}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #1a1a2e; color: white; padding: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 20px 0; }}
        .stat {{ background: #f5f5f5; padding: 15px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; }}
        .risk-{result.risk_assessment['level']} {{ color: {'red' if result.risk_assessment['level'] in ['critical', 'high'] else 'orange' if result.risk_assessment['level'] == 'medium' else 'green'}; }}
        .domain-list {{ background: #f9f9f9; padding: 15px; }}
        .tracker {{ color: red; }}
        .third-party {{ color: orange; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Domain Tree Analysis</h1>
        <p>Target: {result.target_url}</p>
        <p>Captured: {result.captured_at.isoformat()}</p>
    </div>
    
    <div class="stats">
        <div class="stat">
            <div class="stat-value">{len(result.unique_domains)}</div>
            <div>Total Domains</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(result.third_party_domains)}</div>
            <div>Third Parties</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(result.trackers)}</div>
            <div>Trackers</div>
        </div>
        <div class="stat">
            <div class="stat-value risk-{result.risk_assessment['level']}">{result.risk_assessment['score']}</div>
            <div>Risk Score</div>
        </div>
    </div>
    
    <h2>Risk Factors</h2>
    <ul>
        {''.join(f'<li>{factor}</li>' for factor in result.risk_assessment['factors'])}
    </ul>
    
    <h2>Trackers Detected</h2>
    <ul class="domain-list">
        {''.join(f'<li class="tracker">{tracker}</li>' for tracker in result.trackers.keys()) or '<li>None detected</li>'}
    </ul>
    
    <h2>Third-Party Domains</h2>
    <ul class="domain-list">
        {''.join(f'<li class="third-party">{domain}</li>' for domain in result.third_party_domains)}
    </ul>
</body>
</html>
"""
            return html
        
        return None



if __name__ == "__main__":
    collector = DomainTree()
    

    result = collector.capture_url("https://example.com")
    
    print(f"Capture ID: {result.capture_id}")
    print(f"Domains found: {len(result.unique_domains)}")
    print(f"Third-party domains: {len(result.third_party_domains)}")
    print(f"Trackers: {list(result.trackers.keys())}")
    print(f"Risk Score: {result.risk_assessment['score']} ({result.risk_assessment['level']})")
    print(f"\nStatistics: {collector.get_statistics()}")


