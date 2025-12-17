"""
Email Security Compliance Engine

Purpose: Calculate compliance scores for email security standards.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger


class ComplianceEngine:
    """
    Email Security Compliance Engine.
    
    Calculates compliance scores for:
    - RFC 7208 (SPF)
    - RFC 6376 (DKIM)
    - RFC 7489 (DMARC)
    - M3AAWG best practices
    """
    
    def __init__(self):
        """Initialize Compliance Engine."""
        pass
    
    def calculate_compliance(self, email_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive compliance scores.
        
        Args:
            email_config: Email security configuration from EmailAudit
            
        Returns:
            Compliance scores and details
        """
        compliance = {
            "rfc_7208_spf": self._calculate_spf_compliance(email_config.get("spf", {})),
            "rfc_6376_dkim": self._calculate_dkim_compliance(email_config.get("dkim", {})),
            "rfc_7489_dmarc": self._calculate_dmarc_compliance(email_config.get("dmarc", {})),
            "m3aawg": self._calculate_m3aawg_compliance(email_config),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Calculate overall score
        compliance["overall_score"] = (
            compliance["rfc_7208_spf"]["score"] * 0.3 +
            compliance["rfc_6376_dkim"]["score"] * 0.3 +
            compliance["rfc_7489_dmarc"]["score"] * 0.3 +
            compliance["m3aawg"]["score"] * 0.1
        )
        
        compliance["overall_level"] = self._score_to_level(compliance["overall_score"])
        
        return compliance
    
    def _calculate_spf_compliance(self, spf_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate RFC 7208 (SPF) compliance.
        
        Returns:
            Compliance details with score 0-100
        """
        result = {
            "standard": "RFC 7208 (SPF)",
            "compliant": False,
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        if not spf_config.get("exists"):
            result["issues"].append("No SPF record found")
            result["recommendations"].append("Create an SPF record: v=spf1 include:_spf.google.com ~all")
            return result
        
        result["compliant"] = True
        result["score"] = 60  # Base score for having SPF
        
        all_mechanism = spf_config.get("all_mechanism")
        
        if all_mechanism == '-all':
            result["score"] = 100
        elif all_mechanism == '~all':
            result["score"] = 80
            result["issues"].append("SPF uses softfail (~all) instead of hardfail (-all)")
            result["recommendations"].append("Upgrade to -all for strict enforcement")
        elif all_mechanism == '+all':
            result["score"] = 0
            result["issues"].append("SPF uses +all which allows all senders")
            result["recommendations"].append("Change +all to ~all or -all")
        elif all_mechanism is None:
            result["score"] = 50
            result["issues"].append("SPF record missing 'all' mechanism")
            result["recommendations"].append("Add explicit 'all' mechanism")
        
        # Check for too many includes
        includes = spf_config.get("includes", [])
        if len(includes) > 10:
            result["score"] -= 10
            result["issues"].append(f"Too many SPF includes ({len(includes)} > 10)")
            result["recommendations"].append("Consolidate SPF includes or use SPF macros")
        
        return result
    
    def _calculate_dkim_compliance(self, dkim_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate RFC 6376 (DKIM) compliance.
        
        Returns:
            Compliance details with score 0-100
        """
        result = {
            "standard": "RFC 6376 (DKIM)",
            "compliant": False,
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        selectors = dkim_config.get("selectors_found", [])
        
        if not selectors:
            result["issues"].append("No DKIM records found")
            result["recommendations"].append("Configure DKIM signing for your email server")
            return result
        
        result["compliant"] = True
        result["score"] = 100
        
        # Check for multiple selectors (better resilience)
        if len(selectors) == 1:
            result["score"] = 90
            result["issues"].append("Only one DKIM selector found")
            result["recommendations"].append("Consider using multiple DKIM selectors for better resilience")
        
        return result
    
    def _calculate_dmarc_compliance(self, dmarc_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate RFC 7489 (DMARC) compliance.
        
        Returns:
            Compliance details with score 0-100
        """
        result = {
            "standard": "RFC 7489 (DMARC)",
            "compliant": False,
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        if not dmarc_config.get("exists"):
            result["issues"].append("No DMARC record found")
            result["recommendations"].append("Create a DMARC record: v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com")
            return result
        
        result["compliant"] = True
        result["score"] = 50  # Base score for having DMARC
        
        policy = dmarc_config.get("policy")
        
        if policy == 'reject':
            result["score"] = 100
        elif policy == 'quarantine':
            result["score"] = 85
            result["issues"].append("DMARC policy is 'quarantine' (consider 'reject' for stronger protection)")
            result["recommendations"].append("Upgrade to 'reject' policy after monitoring period")
        elif policy == 'none':
            result["score"] = 40
            result["issues"].append("DMARC policy is 'none' (monitoring only)")
            result["recommendations"].append("Upgrade DMARC policy to 'quarantine' or 'reject'")
        
        # Check for aggregate reports
        if not dmarc_config.get("rua"):
            result["score"] -= 10
            result["issues"].append("No aggregate report URI (rua) configured")
            result["recommendations"].append("Add rua= tag to receive DMARC reports")
        
        # Check for forensic reports
        if not dmarc_config.get("ruf"):
            result["score"] -= 5
            result["issues"].append("No forensic report URI (ruf) configured")
            result["recommendations"].append("Add ruf= tag for forensic reports (optional)")
        
        # Check percentage
        pct = dmarc_config.get("pct", 100)
        if pct < 100:
            result["score"] -= 5
            result["issues"].append(f"DMARC only applies to {pct}% of emails")
            result["recommendations"].append("Set pct=100 for full coverage")
        
        return result
    
    def _calculate_m3aawg_compliance(self, email_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate M3AAWG best practices compliance.
        
        Returns:
            Compliance details with score 0-100
        """
        result = {
            "standard": "M3AAWG Best Practices",
            "compliant": False,
            "score": 0,
            "issues": [],
            "recommendations": []
        }
        
        spf = email_config.get("spf", {})
        dkim = email_config.get("dkim", {})
        dmarc = email_config.get("dmarc", {})
        
        score = 0
        max_score = 100
        
        # SPF with -all (25 points)
        if spf.get("exists") and spf.get("all_mechanism") == '-all':
            score += 25
        else:
            result["issues"].append("SPF should use -all for strict enforcement")
            result["recommendations"].append("Configure SPF with -all mechanism")
        
        # DKIM configured (25 points)
        if dkim.get("selectors_found"):
            score += 25
        else:
            result["issues"].append("DKIM should be configured")
            result["recommendations"].append("Configure DKIM signing for all outgoing emails")
        
        # DMARC with quarantine or reject (25 points)
        if dmarc.get("exists") and dmarc.get("policy") in ['quarantine', 'reject']:
            score += 25
        else:
            result["issues"].append("DMARC should be set to quarantine or reject")
            result["recommendations"].append("Upgrade DMARC policy to quarantine or reject")
        
        # DMARC with reporting (25 points)
        if dmarc.get("exists") and dmarc.get("rua"):
            score += 25
        else:
            result["issues"].append("DMARC should include aggregate reporting")
            result["recommendations"].append("Add rua= tag to DMARC record for reporting")
        
        result["score"] = score
        result["compliant"] = score >= 75
        
        return result
    
    def _score_to_level(self, score: float) -> str:
        """Convert score to compliance level.
        
        Args:
            score: Compliance score (0-100)
            
        Returns:
            Compliance level string
        """
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 50:
            return "fair"
        elif score >= 25:
            return "poor"
        else:
            return "critical"
    
    def generate_compliance_report(self, compliance: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed compliance report.
        
        Args:
            compliance: Compliance scores from calculate_compliance
            
        Returns:
            Detailed compliance report
        """
        report = {
            "summary": {
                "overall_score": compliance.get("overall_score", 0),
                "overall_level": compliance.get("overall_level", "unknown"),
                "timestamp": compliance.get("timestamp"),
                "standards_checked": [
                    "RFC 7208 (SPF)",
                    "RFC 6376 (DKIM)",
                    "RFC 7489 (DMARC)",
                    "M3AAWG Best Practices"
                ]
            },
            "standards": {
                "rfc_7208_spf": compliance.get("rfc_7208_spf", {}),
                "rfc_6376_dkim": compliance.get("rfc_6376_dkim", {}),
                "rfc_7489_dmarc": compliance.get("rfc_7489_dmarc", {}),
                "m3aawg": compliance.get("m3aawg", {})
            },
            "recommendations": self._extract_recommendations(compliance)
        }
        
        return report
    
    def _extract_recommendations(self, compliance: Dict[str, Any]) -> List[str]:
        """Extract all recommendations from compliance scores.
        
        Args:
            compliance: Compliance scores
            
        Returns:
            List of unique recommendations
        """
        recommendations = []
        
        for standard_key in ["rfc_7208_spf", "rfc_6376_dkim", "rfc_7489_dmarc", "m3aawg"]:
            standard = compliance.get(standard_key, {})
            recs = standard.get("recommendations", [])
            recommendations.extend(recs)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recs.append(rec)
        
        return unique_recs

