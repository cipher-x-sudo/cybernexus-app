"""
TunnelDetector Collector - HTTP Tunnel Detection

Inspired by: Tunna (https://github.com/SECFORCE/Tunna)

Detects and analyzes HTTP tunneling attempts where TCP traffic
is encapsulated within HTTP requests. Focuses on detection
and analysis rather than providing tunneling capabilities.

Features:
- HTTP tunnel pattern detection
- Traffic anomaly analysis
- Beaconing detection
- Covert channel identification
- Protocol-over-HTTP detection
- Risk scoring

DSA Usage:
- CircularBuffer: Rolling window analysis
- HashMap: Connection state tracking
- Heap: Priority alerting
- Graph: Connection relationship mapping
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import re
import math
from collections import deque

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dsa.circular_buffer import CircularBuffer
from core.dsa.hashmap import HashMap
from core.dsa.heap import MaxHeap
from core.dsa.graph import Graph


class TunnelType(Enum):
    """Types of detected tunnels"""
    HTTP_TUNNEL = "http_tunnel"
    DNS_TUNNEL = "dns_tunnel"
    ICMP_TUNNEL = "icmp_tunnel"
    WEBSOCKET_COVERT = "websocket_covert"
    CHUNKED_ENCODING = "chunked_encoding"
    LONG_POLLING = "long_polling"
    UNKNOWN = "unknown"


class DetectionConfidence(Enum):
    """Confidence levels for detection"""
    CONFIRMED = "confirmed"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SUSPICIOUS = "suspicious"


@dataclass
class HTTPRequest:
    """Represents an HTTP request for analysis"""
    request_id: str
    timestamp: datetime
    source_ip: str
    destination_ip: str
    destination_port: int
    method: str
    uri: str
    host: str
    content_length: int
    headers: Dict[str, str]
    body_entropy: float = 0.0
    response_size: int = 0
    response_time_ms: float = 0
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "method": self.method,
            "uri": self.uri,
            "host": self.host,
            "content_length": self.content_length,
            "body_entropy": self.body_entropy,
            "response_time_ms": self.response_time_ms
        }


@dataclass
class TunnelDetection:
    """A detected tunnel or suspicious pattern"""
    detection_id: str
    tunnel_type: TunnelType
    confidence: DetectionConfidence
    source_ip: str
    destination_ip: str
    destination_port: int
    first_seen: datetime
    last_seen: datetime
    request_count: int
    indicators: List[str]
    risk_score: float
    sample_requests: List[str] = field(default_factory=list)
    
    def __lt__(self, other):
        return self.risk_score < other.risk_score
    
    def to_dict(self) -> Dict:
        return {
            "detection_id": self.detection_id,
            "tunnel_type": self.tunnel_type.value,
            "confidence": self.confidence.value,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "destination_port": self.destination_port,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "request_count": self.request_count,
            "indicators": self.indicators,
            "risk_score": self.risk_score
        }


@dataclass
class BeaconingPattern:
    """Detected beaconing behavior"""
    pattern_id: str
    source_ip: str
    destination: str
    interval_seconds: float
    interval_variance: float
    confidence: float
    sample_count: int
    first_seen: datetime
    last_seen: datetime
    
    def to_dict(self) -> Dict:
        return {
            "pattern_id": self.pattern_id,
            "source_ip": self.source_ip,
            "destination": self.destination,
            "interval_seconds": self.interval_seconds,
            "interval_variance": self.interval_variance,
            "confidence": self.confidence,
            "sample_count": self.sample_count,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat()
        }


class TunnelDetector:
    """
    HTTP Tunnel Detection Collector
    
    Analyzes HTTP traffic to detect tunneling attempts.
    Inspired by understanding how Tunna works to better detect such tools.
    """
    
    # Known tunnel indicators
    TUNNEL_INDICATORS = {
        "unusual_content_type": ["application/octet-stream", "binary/octet-stream"],
        "tunnel_headers": ["X-Tunnel", "X-Forwarded-TCP", "X-Socket-ID"],
        "suspicious_paths": ["/proxy", "/tunnel", "/conn", "/socket", "/relay"],
        "webshell_patterns": [".php?cmd=", ".asp?exec=", ".jsp?c="]
    }
    
    # Tunna-specific patterns
    TUNNA_PATTERNS = [
        r'/conn\?[a-f0-9]+',
        r'cmd=\w+&data=',
        r'action=(read|write|open|close)',
        r'X-CMD:\s*(read|write)'
    ]
    
    def __init__(self, buffer_size: int = 10000):
        """
        Initialize TunnelDetector
        
        Args:
            buffer_size: Size of circular buffer for request history
        """
        # Circular buffer for recent requests (rolling window analysis)
        self.request_buffer = CircularBuffer(buffer_size)
        
        # HashMap for connection tracking
        self.connections = HashMap()  # conn_key -> connection state
        self.requests = HashMap()  # request_id -> HTTPRequest
        
        # MaxHeap for priority detections
        self.detection_queue = MaxHeap()
        
        # Graph for connection relationships
        self.connection_graph = Graph(directed=True)
        
        # Detection storage
        self.detections = HashMap()  # detection_id -> TunnelDetection
        self.beacons = HashMap()  # pattern_id -> BeaconingPattern
        
        # Timing analysis per connection
        self.timing_data = HashMap()  # conn_key -> list of timestamps
        
        # Statistics
        self.stats = {
            "requests_analyzed": 0,
            "tunnels_detected": 0,
            "beacons_detected": 0,
            "alerts_generated": 0
        }
    
    def _generate_id(self, prefix: str, data: str) -> str:
        """Generate unique ID"""
        ts = datetime.now().isoformat()
        return f"{prefix}_{hashlib.md5(f'{data}:{ts}'.encode()).hexdigest()[:10]}"
    
    def _get_connection_key(self, src_ip: str, dst_ip: str, dst_port: int) -> str:
        """Generate connection key"""
        return f"{src_ip}->{dst_ip}:{dst_port}"
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
        
        # Count byte frequencies
        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        length = len(data)
        for count in freq.values():
            p = count / length
            entropy -= p * math.log2(p)
        
        # Normalize to 0-1 range (max entropy for bytes is 8)
        return entropy / 8.0
    
    def analyze_request(
        self,
        source_ip: str,
        destination_ip: str,
        destination_port: int,
        method: str,
        uri: str,
        host: str,
        headers: Dict[str, str],
        body: bytes = b"",
        response_size: int = 0,
        response_time_ms: float = 0
    ) -> Optional[TunnelDetection]:
        """
        Analyze an HTTP request for tunneling indicators
        
        Returns TunnelDetection if suspicious activity detected
        """
        request_id = self._generate_id("req", f"{source_ip}:{uri}")
        
        # Calculate body entropy
        body_entropy = self._calculate_entropy(body) if body else 0.0
        
        # Create request object
        request = HTTPRequest(
            request_id=request_id,
            timestamp=datetime.now(),
            source_ip=source_ip,
            destination_ip=destination_ip,
            destination_port=destination_port,
            method=method,
            uri=uri,
            host=host,
            content_length=len(body),
            headers=headers,
            body_entropy=body_entropy,
            response_size=response_size,
            response_time_ms=response_time_ms,
            user_agent=headers.get("User-Agent")
        )
        
        # Store request
        self.requests.put(request_id, request)
        self.request_buffer.push(request.to_dict())
        
        # Track connection
        conn_key = self._get_connection_key(source_ip, destination_ip, destination_port)
        self._track_connection(conn_key, request)
        
        # Update graph
        if source_ip not in self.connection_graph:
            self.connection_graph.add_node(source_ip, label=source_ip, node_type="ip", data={"type": "client"})
        dest_key = f"{destination_ip}:{destination_port}"
        if dest_key not in self.connection_graph:
            self.connection_graph.add_node(dest_key, label=dest_key, node_type="endpoint", data={"type": "server"})
        self.connection_graph.add_edge(source_ip, dest_key)
        
        self.stats["requests_analyzed"] += 1
        
        # Run detection checks
        indicators = []
        tunnel_type = TunnelType.UNKNOWN
        
        # Check 1: Suspicious headers
        header_indicators = self._check_suspicious_headers(headers)
        indicators.extend(header_indicators)
        
        # Check 2: Suspicious URI patterns
        uri_indicators, detected_type = self._check_uri_patterns(uri)
        indicators.extend(uri_indicators)
        if detected_type:
            tunnel_type = detected_type
        
        # Check 3: High entropy body (encrypted/binary data)
        if body_entropy > 0.9 and len(body) > 100:
            indicators.append(f"High entropy body ({body_entropy:.2f})")
            if tunnel_type == TunnelType.UNKNOWN:
                tunnel_type = TunnelType.HTTP_TUNNEL
        
        # Check 4: Unusual content length patterns
        content_indicators = self._check_content_patterns(request)
        indicators.extend(content_indicators)
        
        # Check 5: Beaconing behavior
        beacon = self._check_beaconing(conn_key)
        if beacon:
            indicators.append(f"Beaconing detected (interval: {beacon.interval_seconds:.1f}s)")
        
        # Check 6: Long-polling pattern
        if response_time_ms > 30000:  # 30+ seconds
            indicators.append("Long-polling behavior")
            if tunnel_type == TunnelType.UNKNOWN:
                tunnel_type = TunnelType.LONG_POLLING
        
        # Create detection if indicators found
        if len(indicators) >= 2:  # Need at least 2 indicators
            detection = self._create_detection(
                conn_key, request, indicators, tunnel_type
            )
            return detection
        
        return None
    
    def _track_connection(self, conn_key: str, request: HTTPRequest):
        """Track connection state and timing"""
        conn_state = self.connections.get(conn_key)
        
        if not conn_state:
            conn_state = {
                "first_seen": request.timestamp,
                "last_seen": request.timestamp,
                "request_count": 0,
                "total_bytes_sent": 0,
                "total_bytes_received": 0,
                "methods": set(),
                "uris": set()
            }
            self.connections.put(conn_key, conn_state)
        
        conn_state["last_seen"] = request.timestamp
        conn_state["request_count"] += 1
        conn_state["total_bytes_sent"] += request.content_length
        conn_state["total_bytes_received"] += request.response_size
        conn_state["methods"].add(request.method)
        conn_state["uris"].add(request.uri)
        
        # Track timing for beaconing detection
        timing = self.timing_data.get(conn_key)
        if timing is None:
            timing = []
            self.timing_data.put(conn_key, timing)
        timing.append(request.timestamp)
        
        # Keep only last 100 timestamps
        if len(timing) > 100:
            timing.pop(0)
    
    def _check_suspicious_headers(self, headers: Dict[str, str]) -> List[str]:
        """Check for suspicious HTTP headers"""
        indicators = []
        
        # Check content type
        content_type = headers.get("Content-Type", "").lower()
        for suspicious in self.TUNNEL_INDICATORS["unusual_content_type"]:
            if suspicious in content_type:
                indicators.append(f"Suspicious Content-Type: {content_type}")
                break
        
        # Check for tunnel-specific headers
        for header in self.TUNNEL_INDICATORS["tunnel_headers"]:
            if header in headers:
                indicators.append(f"Tunnel header found: {header}")
        
        # Check transfer encoding
        if headers.get("Transfer-Encoding", "").lower() == "chunked":
            # Chunked encoding with specific patterns
            if "X-Accel-Buffering" in headers:
                indicators.append("Chunked encoding with buffering disabled")
        
        return indicators
    
    def _check_uri_patterns(self, uri: str) -> Tuple[List[str], Optional[TunnelType]]:
        """Check for suspicious URI patterns"""
        indicators = []
        tunnel_type = None
        
        uri_lower = uri.lower()
        
        # Check suspicious paths
        for path in self.TUNNEL_INDICATORS["suspicious_paths"]:
            if path in uri_lower:
                indicators.append(f"Suspicious path: {path}")
                tunnel_type = TunnelType.HTTP_TUNNEL
        
        # Check webshell patterns
        for pattern in self.TUNNEL_INDICATORS["webshell_patterns"]:
            if pattern in uri_lower:
                indicators.append(f"Webshell pattern: {pattern}")
                tunnel_type = TunnelType.HTTP_TUNNEL
        
        # Check Tunna-specific patterns
        for pattern in self.TUNNA_PATTERNS:
            if re.search(pattern, uri, re.IGNORECASE):
                indicators.append(f"Tunna-like pattern detected")
                tunnel_type = TunnelType.HTTP_TUNNEL
                break
        
        return indicators, tunnel_type
    
    def _check_content_patterns(self, request: HTTPRequest) -> List[str]:
        """Check for suspicious content patterns"""
        indicators = []
        
        # Large POST with small response (data exfil)
        if request.method == "POST" and request.content_length > 10000:
            if request.response_size < 100:
                indicators.append("Large POST with minimal response")
        
        # Rapid small requests (command channel)
        if request.content_length < 50 and request.response_size < 50:
            conn_key = self._get_connection_key(
                request.source_ip, 
                request.destination_ip,
                request.destination_port
            )
            conn = self.connections.get(conn_key)
            if conn and conn["request_count"] > 50:
                indicators.append("Rapid small request pattern")
        
        return indicators
    
    def _check_beaconing(self, conn_key: str) -> Optional[BeaconingPattern]:
        """Check for beaconing behavior"""
        timing = self.timing_data.get(conn_key)
        if not timing or len(timing) < 10:
            return None
        
        # Calculate intervals
        intervals = []
        for i in range(1, len(timing)):
            delta = (timing[i] - timing[i-1]).total_seconds()
            if delta > 0:
                intervals.append(delta)
        
        if len(intervals) < 5:
            return None
        
        # Calculate statistics
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = math.sqrt(variance)
        
        # Coefficient of variation (lower = more regular)
        cv = std_dev / mean_interval if mean_interval > 0 else float('inf')
        
        # Beaconing typically has CV < 0.3 and regular intervals
        if cv < 0.3 and mean_interval < 300:  # Less than 5 min intervals
            confidence = 1.0 - cv
            
            pattern_id = self._generate_id("beacon", conn_key)
            
            # Parse connection key
            parts = conn_key.split("->")
            src_ip = parts[0]
            dest = parts[1] if len(parts) > 1 else "unknown"
            
            pattern = BeaconingPattern(
                pattern_id=pattern_id,
                source_ip=src_ip,
                destination=dest,
                interval_seconds=mean_interval,
                interval_variance=variance,
                confidence=confidence,
                sample_count=len(intervals),
                first_seen=timing[0],
                last_seen=timing[-1]
            )
            
            self.beacons.put(pattern_id, pattern)
            self.stats["beacons_detected"] += 1
            
            return pattern
        
        return None
    
    def _create_detection(
        self,
        conn_key: str,
        request: HTTPRequest,
        indicators: List[str],
        tunnel_type: TunnelType
    ) -> TunnelDetection:
        """Create a tunnel detection"""
        detection_id = self._generate_id("tunnel", conn_key)
        
        # Calculate risk score
        risk_score = min(1.0, len(indicators) * 0.2 + 0.3)
        
        # Boost for specific tunnel types
        if tunnel_type in [TunnelType.HTTP_TUNNEL, TunnelType.CHUNKED_ENCODING]:
            risk_score = min(1.0, risk_score + 0.2)
        
        # Determine confidence
        if risk_score >= 0.8:
            confidence = DetectionConfidence.HIGH
        elif risk_score >= 0.6:
            confidence = DetectionConfidence.MEDIUM
        else:
            confidence = DetectionConfidence.LOW
        
        conn_state = self.connections.get(conn_key)
        
        detection = TunnelDetection(
            detection_id=detection_id,
            tunnel_type=tunnel_type,
            confidence=confidence,
            source_ip=request.source_ip,
            destination_ip=request.destination_ip,
            destination_port=request.destination_port,
            first_seen=conn_state["first_seen"] if conn_state else request.timestamp,
            last_seen=request.timestamp,
            request_count=conn_state["request_count"] if conn_state else 1,
            indicators=indicators,
            risk_score=risk_score,
            sample_requests=[request.request_id]
        )
        
        self.detections.put(detection_id, detection)
        self.detection_queue.push(detection)
        self.stats["tunnels_detected"] += 1
        
        return detection
    
    def get_detections(
        self,
        tunnel_type: Optional[TunnelType] = None,
        min_confidence: DetectionConfidence = DetectionConfidence.LOW,
        limit: int = 50
    ) -> List[TunnelDetection]:
        """Get tunnel detections with filtering"""
        results = []
        confidence_order = [
            DetectionConfidence.SUSPICIOUS,
            DetectionConfidence.LOW,
            DetectionConfidence.MEDIUM,
            DetectionConfidence.HIGH,
            DetectionConfidence.CONFIRMED
        ]
        min_idx = confidence_order.index(min_confidence)
        
        for det_id in self.detections.keys():
            det = self.detections.get(det_id)
            if not det:
                continue
            
            if tunnel_type and det.tunnel_type != tunnel_type:
                continue
            
            det_idx = confidence_order.index(det.confidence)
            if det_idx < min_idx:
                continue
            
            results.append(det)
        
        return sorted(results, key=lambda d: d.risk_score, reverse=True)[:limit]
    
    def get_beaconing_patterns(self, min_confidence: float = 0.5) -> List[BeaconingPattern]:
        """Get detected beaconing patterns"""
        results = []
        
        for pid in self.beacons.keys():
            pattern = self.beacons.get(pid)
            if pattern and pattern.confidence >= min_confidence:
                results.append(pattern)
        
        return sorted(results, key=lambda p: p.confidence, reverse=True)
    
    def get_connection_stats(self, conn_key: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific connection"""
        conn = self.connections.get(conn_key)
        if not conn:
            return None
        
        return {
            "connection": conn_key,
            "first_seen": conn["first_seen"].isoformat(),
            "last_seen": conn["last_seen"].isoformat(),
            "request_count": conn["request_count"],
            "bytes_sent": conn["total_bytes_sent"],
            "bytes_received": conn["total_bytes_received"],
            "methods_used": list(conn["methods"]),
            "unique_uris": len(conn["uris"])
        }
    
    def get_top_talkers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top connections by request count"""
        connections = []
        
        for key in self.connections.keys():
            conn = self.connections.get(key)
            if conn:
                connections.append({
                    "connection": key,
                    "request_count": conn["request_count"],
                    "bytes_sent": conn["total_bytes_sent"],
                    "bytes_received": conn["total_bytes_received"]
                })
        
        return sorted(connections, key=lambda c: c["request_count"], reverse=True)[:limit]
    
    def get_recent_activity(self, minutes: int = 60) -> Dict[str, Any]:
        """Get recent activity summary"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        
        recent_requests = 0
        recent_detections = 0
        
        for det_id in self.detections.keys():
            det = self.detections.get(det_id)
            if det and det.last_seen >= cutoff:
                recent_detections += 1
        
        # Count from buffer
        buffer_data = list(self.request_buffer.get_all())
        for req_data in buffer_data:
            try:
                ts = datetime.fromisoformat(req_data.get("timestamp", ""))
                if ts >= cutoff:
                    recent_requests += 1
            except:
                pass
        
        return {
            "period_minutes": minutes,
            "requests_analyzed": recent_requests,
            "detections": recent_detections,
            "active_connections": len(list(self.connections.keys()))
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics"""
        return {
            **self.stats,
            "active_connections": len(list(self.connections.keys())),
            "buffer_usage": len(self.request_buffer),
            "graph_nodes": self.connection_graph.vertex_count(),
            "graph_edges": self.connection_graph.edge_count()
        }


if __name__ == "__main__":
    detector = TunnelDetector()
    
    # Simulate suspicious traffic
    for i in range(20):
        detection = detector.analyze_request(
            source_ip="192.168.1.100",
            destination_ip="10.0.0.50",
            destination_port=80,
            method="POST",
            uri=f"/proxy/conn?session={i:04x}",
            host="webserver.internal",
            headers={
                "Content-Type": "application/octet-stream",
                "X-Tunnel": "active"
            },
            body=bytes([i % 256] * 1000),
            response_size=50,
            response_time_ms=100
        )
        
        if detection:
            print(f"Detection: {detection.tunnel_type.value} - {detection.confidence.value}")
            print(f"  Indicators: {detection.indicators}")
    
    print(f"\nStatistics: {detector.get_statistics()}")
    print(f"\nBeaconing patterns: {len(detector.get_beaconing_patterns())}")


