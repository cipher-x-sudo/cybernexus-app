from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from app.core.dsa import MaxHeap, HashMap


class SeverityLevel(Enum):
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1


class ThreatRanker:
    def __init__(self):
        self._threat_heap = MaxHeap()
        self._threats = HashMap()
        self._scores = HashMap()
    
    def calculate_score(self, threat: Dict[str, Any]) -> float:
        score = 0.0
        
        severity = threat.get("severity", "info").lower()
        severity_weights = {
            "critical": 50,
            "high": 40,
            "medium": 25,
            "low": 10,
            "info": 5
        }
        score += severity_weights.get(severity, 5)
        
        cvss = threat.get("cvss_score", threat.get("score", 0))
        if cvss:
            score += (cvss / 10) * 30
        
        created_at = threat.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = None
            
            if created_at:
                age_hours = (datetime.utcnow() - created_at.replace(tzinfo=None)).total_seconds() / 3600
                if age_hours < 1:
                    score += 10
                elif age_hours < 24:
                    score += 7
                elif age_hours < 168:  # 1 week
                    score += 4
                else:
                    score += 1
        

        affected = len(threat.get("affected_entities", []))
        score += min(10, affected * 2)
        

        if threat.get("indicators"):
            score += 5
        

        status = threat.get("status", "active").lower()
        if status == "active":
            score *= 1.2
        elif status == "investigating":
            score *= 1.1
        elif status in ["mitigated", "resolved"]:
            score *= 0.5
        elif status == "false_positive":
            score *= 0.1
        
        return round(score, 2)
    
    def add_threat(self, threat_id: str, threat: Dict[str, Any]):
        
        score = self.calculate_score(threat)
        
        self._threats.put(threat_id, threat)
        self._scores.put(threat_id, score)
        self._threat_heap.push(score, threat_id)
    
    def update_threat(self, threat_id: str, updates: Dict[str, Any]):
        
        existing = self._threats.get(threat_id)
        if not existing:
            return
        

        existing.update(updates)
        

        new_score = self.calculate_score(existing)
        self._scores.put(threat_id, new_score)
        

        self._threat_heap.push(new_score, threat_id)
    
    def get_top_threats(self, n: int = 10) -> List[Dict[str, Any]]:
        

        temp_heap = MaxHeap()
        for score, threat_id in self._threat_heap.to_list():
            temp_heap.push(score, threat_id)
        
        results = []
        seen = set()
        
        while len(results) < n and temp_heap:
            item = temp_heap.pop()
            if not item:
                break
            
            score, threat_id = item
            

            if threat_id in seen:
                continue
            seen.add(threat_id)
            

            current_score = self._scores.get(threat_id)
            if current_score != score:
                continue
            
            threat = self._threats.get(threat_id)
            if threat:
                results.append({
                    "threat_id": threat_id,
                    "score": score,
                    "threat": threat
                })
        
        return results
    
    def get_threats_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        
        results = []
        
        for threat_id in self._threats.keys():
            threat = self._threats.get(threat_id)
            if threat and threat.get("severity", "").lower() == severity.lower():
                results.append({
                    "threat_id": threat_id,
                    "score": self._scores.get(threat_id, 0),
                    "threat": threat
                })
        

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    def get_score(self, threat_id: str) -> Optional[float]:
        
        return self._scores.get(threat_id)
    
    def remove_threat(self, threat_id: str):
        
        self._threats.remove(threat_id)
        self._scores.remove(threat_id)

    
    def stats(self) -> Dict[str, Any]:
        
        severity_counts = {}
        total_score = 0
        
        for threat_id in self._threats.keys():
            threat = self._threats.get(threat_id)
            if threat:
                sev = threat.get("severity", "unknown")
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
                total_score += self._scores.get(threat_id, 0)
        
        count = len(self._threats)
        return {
            "total_threats": count,
            "average_score": total_score / count if count else 0,
            "by_severity": severity_counts
        }


