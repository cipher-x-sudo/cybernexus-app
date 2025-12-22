"""Threat ranking and prioritization engine.

This module provides threat scoring and ranking functionality using priority queues
to identify and prioritize the most critical security threats.

This module uses the following DSA concepts from app.core.dsa:
- MaxHeap: Priority queue for threat ranking with highest scores at top
- HashMap: Threat storage and score tracking for O(1) lookups and updates
"""

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
                elif age_hours < 168:
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
        """Add a threat to the ranking system.
        
        DSA-USED:
        - HashMap: Threat and score storage for O(1) lookups
        - MaxHeap: Priority queue insertion for ranking
        
        Args:
            threat_id: Unique threat identifier
            threat: Threat dictionary with details
        """
        score = self.calculate_score(threat)
        
        self._threats.put(threat_id, threat)  # DSA-USED: HashMap
        self._scores.put(threat_id, score)  # DSA-USED: HashMap
        self._threat_heap.push(score, threat_id)  # DSA-USED: MaxHeap
    
    def update_threat(self, threat_id: str, updates: Dict[str, Any]):
        """Update an existing threat and recalculate ranking.
        
        DSA-USED:
        - HashMap: Threat retrieval and score update
        - MaxHeap: Priority queue update with new score
        
        Args:
            threat_id: Threat identifier to update
            updates: Dictionary of fields to update
        """
        existing = self._threats.get(threat_id)  # DSA-USED: HashMap
        if not existing:
            return
        

        existing.update(updates)
        

        new_score = self.calculate_score(existing)
        self._scores.put(threat_id, new_score)  # DSA-USED: HashMap
        

        self._threat_heap.push(new_score, threat_id)  # DSA-USED: MaxHeap
    
    def get_top_threats(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N threats by score using priority queue.
        
        DSA-USED:
        - MaxHeap: Priority queue operations for top-N retrieval
        - HashMap: Threat and score lookups
        
        Args:
            n: Number of top threats to return
        
        Returns:
            List of threat dictionaries sorted by score (highest first)
        """
        temp_heap = MaxHeap()  # DSA-USED: MaxHeap
        for score, threat_id in self._threat_heap.to_list():  # DSA-USED: MaxHeap
            temp_heap.push(score, threat_id)  # DSA-USED: MaxHeap
        
        results = []
        seen = set()
        
        while len(results) < n and temp_heap:  # DSA-USED: MaxHeap
            item = temp_heap.pop()  # DSA-USED: MaxHeap
            if not item:
                break
            
            score, threat_id = item
            

            if threat_id in seen:
                continue
            seen.add(threat_id)
            

            current_score = self._scores.get(threat_id)  # DSA-USED: HashMap
            if current_score != score:
                continue
            
            threat = self._threats.get(threat_id)  # DSA-USED: HashMap
            if threat:
                results.append({
                    "threat_id": threat_id,
                    "score": score,
                    "threat": threat
                })
        
        return results
    
    def get_threats_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get all threats of a specific severity level.
        
        DSA-USED:
        - HashMap: Iteration and lookup operations
        
        Args:
            severity: Severity level to filter by
        
        Returns:
            List of threat dictionaries sorted by score (highest first)
        """
        results = []
        
        for threat_id in self._threats.keys():  # DSA-USED: HashMap
            threat = self._threats.get(threat_id)  # DSA-USED: HashMap
            if threat and threat.get("severity", "").lower() == severity.lower():
                results.append({
                    "threat_id": threat_id,
                    "score": self._scores.get(threat_id, 0),  # DSA-USED: HashMap
                    "threat": threat
                })
        

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    def get_score(self, threat_id: str) -> Optional[float]:
        """Get the current score for a threat.
        
        DSA-USED:
        - HashMap: O(1) score lookup
        
        Args:
            threat_id: Threat identifier
        
        Returns:
            Current threat score, or None if not found
        """
        return self._scores.get(threat_id)  # DSA-USED: HashMap
    
    def remove_threat(self, threat_id: str):
        """Remove a threat from the ranking system.
        
        DSA-USED:
        - HashMap: Threat and score removal
        
        Args:
            threat_id: Threat identifier to remove
        """
        self._threats.remove(threat_id)  # DSA-USED: HashMap
        self._scores.remove(threat_id)  # DSA-USED: HashMap

    
    def stats(self) -> Dict[str, Any]:
        """Get statistics about ranked threats.
        
        DSA-USED:
        - HashMap: Iteration and lookup for statistics calculation
        
        Returns:
            Dictionary with threat statistics
        """
        severity_counts = {}
        total_score = 0
        
        for threat_id in self._threats.keys():  # DSA-USED: HashMap
            threat = self._threats.get(threat_id)  # DSA-USED: HashMap
            if threat:
                sev = threat.get("severity", "unknown")
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
                total_score += self._scores.get(threat_id, 0)  # DSA-USED: HashMap
        
        count = len(self._threats)  # DSA-USED: HashMap
        return {
            "total_threats": count,
            "average_score": total_score / count if count else 0,
            "by_severity": severity_counts
        }


