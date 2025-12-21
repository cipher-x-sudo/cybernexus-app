"""
Tunnel Analyzer Service

Wrapper around TunnelDetector for real-time tunnel pattern detection.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from app.config import settings
from app.collectors.tunnel_detector import TunnelDetector, HTTPRequest


class TunnelAnalyzer:
    """Service for real-time tunnel detection analysis."""
    
    def __init__(self):
        self.detector = TunnelDetector(buffer_size=10000)
        self.confidence_threshold = settings.NETWORK_TUNNEL_CONFIDENCE_THRESHOLD.lower()
    
    async def analyze_request(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a request log entry for tunnel patterns.
        
        Args:
            log_entry: Network log entry with request/response data
            
        Returns:
            Tunnel detection result or None if no tunnel detected
        """
        if not settings.NETWORK_ENABLE_TUNNEL_DETECTION:
            return None
        
        try:
            # Extract request data
            source_ip = log_entry.get("ip", "unknown")
            method = log_entry.get("method", "GET")
            path = log_entry.get("path", "")
            query = log_entry.get("query", "")
            uri = f"{path}?{query}" if query else path
            host = log_entry.get("headers", {}).get("host", "")
            headers = log_entry.get("headers", {})
            body = log_entry.get("body", "").encode("utf-8")
            response_size = log_entry.get("response_body_size", 0)
            response_time_ms = log_entry.get("response_time_ms", 0)
            
            # Create HTTPRequest object for TunnelDetector
            request_id = log_entry.get("id", "")
            request = HTTPRequest(
                request_id=request_id,
                timestamp=datetime.fromisoformat(log_entry.get("timestamp", datetime.utcnow().isoformat())),
                source_ip=source_ip,
                destination_ip="",  # Not available in log
                destination_port=0,  # Not available in log
                method=method,
                uri=uri,
                host=host,
                content_length=len(body),
                headers=headers,
                body_entropy=0.0,  # Will be calculated by detector
                response_size=response_size,
                response_time_ms=response_time_ms,
                user_agent=headers.get("user-agent")
            )
            
            # Analyze request
            detection = self.detector.analyze_request(
                source_ip=source_ip,
                destination_ip="",  # Not available
                destination_port=0,  # Not available
                method=method,
                uri=uri,
                host=host,
                headers=headers,
                body=body,
                response_size=response_size,
                response_time_ms=response_time_ms
            )
            
            if not detection:
                return None
            
            # Check confidence threshold
            confidence_levels = {"low": 1, "medium": 2, "high": 3, "confirmed": 4}
            detection_confidence = detection.confidence.value.lower()
            threshold_level = confidence_levels.get(self.confidence_threshold, 2)
            detection_level = confidence_levels.get(detection_confidence, 1)
            
            if detection_level < threshold_level:
                return None
            
            # Convert to dictionary
            detection_dict = {
                "detected": True,
                "tunnel_type": detection.tunnel_type.value,
                "confidence": detection.confidence.value,
                "risk_score": detection.risk_score,
                "indicators": detection.indicators,
                "detection_id": detection.detection_id,
                "source_ip": detection.source_ip,
                "first_seen": detection.first_seen.isoformat(),
                "last_seen": detection.last_seen.isoformat(),
                "request_count": detection.request_count
            }
            
            return detection_dict
            
        except Exception as e:
            logger.error(f"Tunnel analysis error: {e}", exc_info=True)
            return None
    
    def get_detector_stats(self) -> Dict[str, Any]:
        """Get statistics from tunnel detector."""
        try:
            return {
                "requests_analyzed": self.detector.stats.get("requests_analyzed", 0),
                "tunnels_detected": self.detector.stats.get("tunnels_detected", 0),
                "beacons_detected": self.detector.stats.get("beacons_detected", 0),
                "alerts_generated": self.detector.stats.get("alerts_generated", 0)
            }
        except Exception as e:
            logger.error(f"Error getting detector stats: {e}")
            return {}


# Global tunnel analyzer instance
_tunnel_analyzer: Optional[TunnelAnalyzer] = None


def get_tunnel_analyzer() -> TunnelAnalyzer:
    """Get or create global tunnel analyzer instance."""
    global _tunnel_analyzer
    if _tunnel_analyzer is None:
        _tunnel_analyzer = TunnelAnalyzer()
    return _tunnel_analyzer




