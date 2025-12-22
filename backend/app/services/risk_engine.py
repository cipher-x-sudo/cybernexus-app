from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger

from app.core.dsa import HashMap, AVLTree, CircularBuffer


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class RiskFactor:
    category: str
    weight: float
    score: float
    findings_count: int
    description: str
    trend: str


@dataclass
class RiskScore:
    target: str
    overall_score: float
    risk_level: RiskLevel
    factors: List[RiskFactor]
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    last_updated: datetime
    trend: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "overall_score": round(self.overall_score, 1),
            "risk_level": self.risk_level.value,
            "factors": [
                {
                    "category": f.category,
                    "weight": f.weight,
                    "score": round(f.score, 1),
                    "findings_count": f.findings_count,
                    "description": f.description,
                    "trend": f.trend
                }
                for f in self.factors
            ],
            "issues": {
                "critical": self.critical_issues,
                "high": self.high_issues,
                "medium": self.medium_issues,
                "low": self.low_issues,
                "total": self.critical_issues + self.high_issues + self.medium_issues + self.low_issues
            },
            "last_updated": self.last_updated.isoformat(),
            "trend": self.trend
        }


class RiskEngine:
    CATEGORY_WEIGHTS = {
        "exposure": 0.20,
        "dark_web": 0.20,
        "email_security": 0.15,
        "infrastructure": 0.20,
        "authentication": 0.15,
        "network": 0.10
    }
    
    SEVERITY_IMPACTS = {
        "critical": 25,
        "high": 15,
        "medium": 8,
        "low": 3,
        "info": 1
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
        self._score_history = HashMap()
        
        self._category_scores = HashMap()
        
        self._findings_by_target = HashMap()
        
        self._global_stats = {
            "targets_tracked": 0,
            "avg_score": 0,
            "total_critical": 0,
            "total_high": 0
        }
        
        logger.info("Risk Engine initialized")
    
    def calculate_risk_score(
        self,
        target: str,
        findings: List[Dict[str, Any]]
    ) -> RiskScore:
        category_scores = {cat: 100.0 for cat in self.CATEGORY_WEIGHTS.keys()}
        category_findings = {cat: [] for cat in self.CATEGORY_WEIGHTS.keys()}
        
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for finding in findings:
            capability = finding.get("capability", "")
            severity = finding.get("severity", "info").lower()
            
            category = self.CAPABILITY_TO_CATEGORY.get(capability, "exposure")
            
            impact = self.SEVERITY_IMPACTS.get(severity, 1)
            category_scores[category] = max(0, category_scores[category] - impact)
            
            category_findings[category].append(finding)
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        

        overall_score = 0.0
        factors = []
        
        for category, weight in self.CATEGORY_WEIGHTS.items():
            cat_score = category_scores[category]
            overall_score += cat_score * weight
            

            trend = self._calculate_trend(target, category, cat_score)
            
            factors.append(RiskFactor(
                category=category,
                weight=weight,
                score=cat_score,
                findings_count=len(category_findings[category]),
                description=self._get_category_description(category, cat_score),
                trend=trend
            ))
        

        risk_level = self._score_to_risk_level(overall_score)
        

        overall_trend = self._calculate_overall_trend(target, overall_score)
        

        risk_score = RiskScore(
            target=target,
            overall_score=overall_score,
            risk_level=risk_level,
            factors=factors,
            critical_issues=severity_counts["critical"],
            high_issues=severity_counts["high"],
            medium_issues=severity_counts["medium"],
            low_issues=severity_counts["low"],
            last_updated=datetime.now(),
            trend=overall_trend
        )
        

        self._store_score(target, risk_score)
        

        self._category_scores.put(target, category_scores)
        

        self._findings_by_target.put(target, findings)
        
        logger.info(f"Calculated risk score for {target}: {overall_score:.1f} ({risk_level.value})")
        
        return risk_score
    
    def _score_to_risk_level(self, score: float) -> RiskLevel:
        if score >= 90:
            return RiskLevel.MINIMAL
        elif score >= 75:
            return RiskLevel.LOW
        elif score >= 50:
            return RiskLevel.MEDIUM
        elif score >= 25:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _get_category_description(self, category: str, score: float) -> str:
        descriptions = {
            "exposure": {
                "good": "Minimal public exposure detected",
                "medium": "Some sensitive information may be publicly accessible",
                "bad": "Significant data exposure found online"
            },
            "dark_web": {
                "good": "No concerning dark web mentions found",
                "medium": "Some dark web activity detected",
                "bad": "Critical dark web threats identified"
            },
            "email_security": {
                "good": "Email authentication properly configured",
                "medium": "Email security has some gaps",
                "bad": "Email highly vulnerable to spoofing"
            },
            "infrastructure": {
                "good": "Infrastructure securely configured",
                "medium": "Some misconfigurations detected",
                "bad": "Critical infrastructure vulnerabilities found"
            },
            "authentication": {
                "good": "Strong authentication practices",
                "medium": "Authentication could be improved",
                "bad": "Weak credentials detected"
            },
            "network": {
                "good": "Network security is solid",
                "medium": "Some network risks identified",
                "bad": "Network vulnerable to covert access"
            }
        }
        
        cat_desc = descriptions.get(category, {})
        
        if score >= 75:
            return cat_desc.get("good", "Good")
        elif score >= 40:
            return cat_desc.get("medium", "Needs attention")
        else:
            return cat_desc.get("bad", "Critical issues")
    
    def _calculate_trend(self, target: str, category: str, current_score: float) -> str:
        history = self._score_history.get(target)
        if not history or len(history) < 2:
            return "stable"
        
        previous = history.get(-2) if len(history) >= 2 else None
        if not previous:
            return "stable"
        
        prev_cat_scores = self._category_scores.get(target)
        if not prev_cat_scores:
            return "stable"
        
        prev_score = prev_cat_scores.get(category, current_score)
        
        diff = current_score - prev_score
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "worsening"
        return "stable"
    
    def _calculate_overall_trend(self, target: str, current_score: float) -> str:
        history = self._score_history.get(target)
        if not history or len(history) < 2:
            return "stable"
        
        scores = list(history)
        if len(scores) < 2:
            return "stable"
        
        prev_score = scores[-2].overall_score if hasattr(scores[-2], 'overall_score') else scores[-2]
        
        diff = current_score - prev_score
        if diff > 3:
            return "improving"
        elif diff < -3:
            return "worsening"
        return "stable"
    
    def _store_score(self, target: str, score: RiskScore):
        history = self._score_history.get(target)
        if not history:
            history = CircularBuffer(capacity=100)
            self._score_history.put(target, history)
        
        history.push(score)
        
        self._update_global_stats()
    
    def _update_global_stats(self):
        total_score = 0
        count = 0
        total_critical = 0
        total_high = 0
        
        for target in self._score_history.keys():
            history = self._score_history.get(target)
            if history and len(history) > 0:
                latest = history.get(-1)
                if latest:
                    total_score += latest.overall_score
                    count += 1
                    total_critical += latest.critical_issues
                    total_high += latest.high_issues
        
        self._global_stats = {
            "targets_tracked": count,
            "avg_score": total_score / count if count > 0 else 0,
            "total_critical": total_critical,
            "total_high": total_high
        }
    
    def get_risk_score(self, target: str) -> Optional[RiskScore]:
        history = self._score_history.get(target)
        if history and len(history) > 0:
            return history.get(-1)
        return None
    
    def get_risk_history(
        self,
        target: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        history = self._score_history.get(target)
        if not history:
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        results = []
        
        for score in history:
            if score.last_updated >= cutoff:
                results.append({
                    "score": score.overall_score,
                    "risk_level": score.risk_level.value,
                    "timestamp": score.last_updated.isoformat()
                })
        
        return results
    
    def get_category_breakdown(self, target: str) -> Dict[str, Any]:
        risk_score = self.get_risk_score(target)
        if not risk_score:
            return {}
        
        return {
            "target": target,
            "overall_score": risk_score.overall_score,
            "categories": {
                factor.category: {
                    "score": factor.score,
                    "weight": factor.weight,
                    "weighted_contribution": factor.score * factor.weight,
                    "findings_count": factor.findings_count,
                    "description": factor.description,
                    "trend": factor.trend
                }
                for factor in risk_score.factors
            }
        }
    
    def get_top_risks(self, target: str, limit: int = 5) -> List[Dict[str, Any]]:
        risk_score = self.get_risk_score(target)
        if not risk_score:
            return []
        
        sorted_factors = sorted(risk_score.factors, key=lambda f: f.score)
        
        return [
            {
                "category": f.category,
                "score": f.score,
                "findings_count": f.findings_count,
                "description": f.description,
                "recommendations": self._get_category_recommendations(f.category, f.score)
            }
            for f in sorted_factors[:limit]
        ]
    
    def _get_category_recommendations(self, category: str, score: float) -> List[str]:
        recommendations = {
            "exposure": [
                "Review and restrict publicly accessible resources",
                "Implement data loss prevention controls",
                "Audit search engine indexed content"
            ],
            "dark_web": [
                "Monitor for leaked credentials continuously",
                "Implement brand protection measures",
                "Set up dark web alerting"
            ],
            "email_security": [
                "Configure strict DMARC policy (reject)",
                "Ensure DKIM is properly configured",
                "Review SPF record for accuracy"
            ],
            "infrastructure": [
                "Patch vulnerable systems immediately",
                "Review and harden server configurations",
                "Implement regular vulnerability scanning"
            ],
            "authentication": [
                "Enforce strong password policies",
                "Implement multi-factor authentication",
                "Review and rotate credentials"
            ],
            "network": [
                "Monitor for tunneling attempts",
                "Review firewall rules",
                "Implement network segmentation"
            ]
        }
        
        if score >= 75:
            return ["Continue current security practices"]
        
        return recommendations.get(category, ["Review security configuration"])
    
    def get_global_stats(self) -> Dict[str, Any]:
        return self._global_stats
    
    def compare_targets(self, targets: List[str]) -> Dict[str, Any]:
        comparison = {
            "targets": [],
            "best_performer": None,
            "worst_performer": None,
            "average_score": 0
        }
        
        total_score = 0
        best_score = -1
        worst_score = 101
        
        for target in targets:
            risk_score = self.get_risk_score(target)
            if risk_score:
                score_data = {
                    "target": target,
                    "score": risk_score.overall_score,
                    "risk_level": risk_score.risk_level.value,
                    "critical_issues": risk_score.critical_issues
                }
                comparison["targets"].append(score_data)
                total_score += risk_score.overall_score
                
                if risk_score.overall_score > best_score:
                    best_score = risk_score.overall_score
                    comparison["best_performer"] = target
                
                if risk_score.overall_score < worst_score:
                    worst_score = risk_score.overall_score
                    comparison["worst_performer"] = target
        
        if comparison["targets"]:
            comparison["average_score"] = total_score / len(comparison["targets"])
        
        return comparison


_risk_engine: Optional[RiskEngine] = None


def get_risk_engine() -> RiskEngine:
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine



