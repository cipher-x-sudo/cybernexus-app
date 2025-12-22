"""Positive scoring system for security improvements.

This module provides scoring for positive security indicators and improvements.
Does not use custom DSA structures.

This module does not use custom DSA concepts from app.core.dsa.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from loguru import logger
import uuid

if TYPE_CHECKING:
    from app.services.orchestrator import Capability


class PositiveScorer:
    POSITIVE_POINTS = {
        "strong_email_config": 10,
        "no_vulnerabilities": 5,
        "improvement_trend": 3,
        "sustained_good_practices": 5,
        "remediated_critical": 25,
        "remediated_high": 12,
        "remediated_medium": 6,
        "remediated_low": 3,
    }
    
    CAPABILITY_TO_CATEGORY = {
        "exposure_discovery": "exposure",
        "dark_web_intelligence": "dark_web",
        "email_security": "email_security",
        "infrastructure_testing": "infrastructure",
        "network_security": "network",
        "investigation": "exposure"
    }
    
    def __init__(self):
        logger.info("Positive Scorer initialized")
    
    def detect_strong_email_config(self, email_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect if email security configuration is strong (SPF, DKIM, DMARC all pass).
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            email_results: Dictionary containing email security test results
        
        Returns:
            Positive indicator dictionary if configuration is strong, None otherwise
        """
        spf_ok = email_results.get("spf", {}).get("status") == "pass" or email_results.get("spf_valid", False)
        dkim_ok = email_results.get("dkim", {}).get("status") == "pass" or email_results.get("dkim_valid", False)
        dmarc_ok = email_results.get("dmarc", {}).get("status") == "pass" or email_results.get("dmarc_valid", False)
        
        if spf_ok and dkim_ok and dmarc_ok:
            return {
                "id": str(uuid.uuid4()),
                "indicator_type": "strong_email_config",
                "category": "email_security",
                "points_awarded": self.POSITIVE_POINTS["strong_email_config"],
                "description": "Email security configuration is strong: SPF, DKIM, and DMARC all properly configured",
                "evidence": {
                    "spf": spf_ok,
                    "dkim": dkim_ok,
                    "dmarc": dmarc_ok
                }
            }
        
        return None
    
    def detect_no_vulnerabilities(self, capability: "Capability", findings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detect if no vulnerabilities were found for a capability.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            capability: The capability that was scanned
            findings: List of findings from the scan
        
        Returns:
            Positive indicator dictionary if no vulnerabilities found, None otherwise
        """
        if len(findings) == 0:
            category = self.CAPABILITY_TO_CATEGORY.get(capability.value, "exposure")
            return {
                "id": str(uuid.uuid4()),
                "indicator_type": "no_vulnerabilities",
                "category": category,
                "points_awarded": self.POSITIVE_POINTS["no_vulnerabilities"],
                "description": f"No vulnerabilities found in {capability.value.replace('_', ' ').title()}",
                "evidence": {
                    "capability": capability.value,
                    "findings_count": 0
                }
            }
        
        return None
    
    def calculate_improvement_trend(self, current_score: float, previous_score: Optional[float]) -> Optional[Dict[str, Any]]:
        """Calculate improvement trend based on score changes.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            current_score: The current security score
            previous_score: The previous security score for comparison
        
        Returns:
            Positive indicator dictionary if score improved, None otherwise
        """
        if previous_score is None or previous_score <= 0:
            return None
        
        if current_score <= previous_score:
            return None
        
        increase = current_score - previous_score
        percentage_increase = (increase / previous_score) * 100 if previous_score > 0 else 0
        
        points = int(percentage_increase / 10) * self.POSITIVE_POINTS["improvement_trend"]
        
        if points > 0:
            return {
                "id": str(uuid.uuid4()),
                "indicator_type": "improvement_trend",
                "category": "general",
                "points_awarded": points,
                "description": f"Security score improved by {increase:.1f} points ({percentage_increase:.1f}%)",
                "evidence": {
                    "previous_score": previous_score,
                    "current_score": current_score,
                    "increase": increase,
                    "percentage_increase": percentage_increase
                }
            }
        
        return None
    
    def create_remediated_indicator(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Create a positive indicator for a remediated finding.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            finding: Dictionary containing finding information
        
        Returns:
            Positive indicator dictionary with points awarded based on severity
        """
        severity = finding.get("severity", "").lower()
        points_key = f"remediated_{severity}"
        points = self.POSITIVE_POINTS.get(points_key, 0)
        
        if points == 0:
            points = 2
        
        capability = finding.get("capability", "unknown")
        category = self.CAPABILITY_TO_CATEGORY.get(capability, "exposure")
        
        return {
            "id": str(uuid.uuid4()),
            "indicator_type": "remediated",
            "category": category,
            "points_awarded": points,
            "description": f"Resolved {severity} finding: {finding.get('title', 'Unknown')}",
            "evidence": {
                "finding_id": finding.get("id"),
                "severity": severity,
                "capability": capability
            }
        }
    
    def analyze_scan_results(self, capability: "Capability", findings: List[Dict[str, Any]], 
                            scan_results: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Analyze scan results and generate positive indicators.
        
        DSA-USED:
        - None: This function does not use custom DSA structures from app.core.dsa.
        
        Args:
            capability: The capability that was scanned
            findings: List of findings from the scan
            scan_results: Optional additional scan result data (used for email security)
        
        Returns:
            List of positive indicator dictionaries
        """
        indicators = []
        
        no_vuln_indicator = self.detect_no_vulnerabilities(capability, findings)
        if no_vuln_indicator:
            indicators.append(no_vuln_indicator)
        
        from app.services.orchestrator import Capability
        if capability == Capability.EMAIL_SECURITY and scan_results:
            email_indicator = self.detect_strong_email_config(scan_results)
            if email_indicator:
                indicators.append(email_indicator)
        
        return indicators


_positive_scorer: Optional[PositiveScorer] = None


def get_positive_scorer() -> PositiveScorer:
    global _positive_scorer
    if _positive_scorer is None:
        _positive_scorer = PositiveScorer()
    return _positive_scorer

