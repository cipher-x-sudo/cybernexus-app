"""
KeywordMonitor Collector - Keyword & Brand Monitoring

Inspired by: VigilantOnion (https://github.com/andreyglauzer/VigilantOnion)

This collector monitors various sources for keyword matches,
providing alerting and scoring based on YARA-like rules.

Features:
- Multi-source keyword monitoring
- Priority-based alerting
- YARA-like pattern matching
- Scoring system for matches
- Historical trend analysis
- Real-time notifications

DSA Usage:
- Trie: Efficient keyword prefix matching
- Heap: Priority queue for alerts
- LinkedList: Match history timeline
- HashMap: Rule storage and lookups
"""

from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import re
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dsa.trie import Trie
from core.dsa.heap import MaxHeap
from core.dsa.linked_list import DoublyLinkedList
from core.dsa.hashmap import HashMap


class MatchSeverity(Enum):
    """Severity levels for keyword matches"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1


class SourceType(Enum):
    """Types of monitored sources"""
    DARK_WEB = "dark_web"
    PASTE_SITE = "paste_site"
    FORUM = "forum"
    SOCIAL_MEDIA = "social_media"
    NEWS = "news"
    CODE_REPO = "code_repo"
    BREACH_DB = "breach_database"


@dataclass
class MonitorRule:
    """A monitoring rule with keywords and conditions"""
    rule_id: str
    name: str
    keywords: List[str]
    regex_patterns: List[str] = field(default_factory=list)
    severity: MatchSeverity = MatchSeverity.MEDIUM
    enabled: bool = True
    case_sensitive: bool = False
    require_all: bool = False  # Require all keywords to match
    exclude_keywords: List[str] = field(default_factory=list)
    source_filter: List[SourceType] = field(default_factory=list)
    score_multiplier: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "keywords": self.keywords,
            "regex_patterns": self.regex_patterns,
            "severity": self.severity.name,
            "enabled": self.enabled,
            "case_sensitive": self.case_sensitive,
            "require_all": self.require_all,
            "exclude_keywords": self.exclude_keywords,
            "source_filter": [s.value for s in self.source_filter],
            "score_multiplier": self.score_multiplier
        }


@dataclass
class KeywordMatch:
    """A keyword match result"""
    match_id: str
    rule_id: str
    rule_name: str
    matched_keywords: List[str]
    matched_patterns: List[str]
    content_snippet: str
    source_url: str
    source_type: SourceType
    severity: MatchSeverity
    score: float
    discovered_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        # For heap comparison - higher score = higher priority
        return self.score < other.score
    
    def to_dict(self) -> Dict:
        return {
            "match_id": self.match_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "matched_keywords": self.matched_keywords,
            "matched_patterns": self.matched_patterns,
            "content_snippet": self.content_snippet[:500],
            "source_url": self.source_url,
            "source_type": self.source_type.value,
            "severity": self.severity.name,
            "score": self.score,
            "discovered_at": self.discovered_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class Alert:
    """An alert generated from high-priority matches"""
    alert_id: str
    match_id: str
    title: str
    description: str
    severity: MatchSeverity
    score: float
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    def __lt__(self, other):
        return self.score < other.score
    
    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "match_id": self.match_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.name,
            "score": self.score,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }


class KeywordMonitor:
    """
    Keyword & Brand Monitoring Collector
    
    Monitors content sources for keyword matches with scoring.
    Inspired by VigilantOnion's dark web monitoring approach.
    """
    
    def __init__(self):
        # Trie for efficient keyword matching
        self.keyword_trie = Trie()
        
        # HashMap for rule storage
        self.rules = HashMap()  # rule_id -> MonitorRule
        
        # MaxHeap for priority alerts (highest score first)
        self.alert_queue = MaxHeap()
        
        # LinkedList for match history
        self.match_history = DoublyLinkedList()
        
        # HashMap for matches and alerts
        self.matches = HashMap()  # match_id -> KeywordMatch
        self.alerts = HashMap()  # alert_id -> Alert
        
        # Keyword to rule mapping for fast lookups
        self.keyword_rules = HashMap()  # keyword -> List[rule_id]
        
        # Statistics
        self.stats = {
            "rules_count": 0,
            "total_matches": 0,
            "total_alerts": 0,
            "content_scanned": 0
        }
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[Alert], None]] = []
    
    def _generate_id(self, prefix: str, data: str) -> str:
        """Generate unique ID"""
        timestamp = datetime.now().isoformat()
        return f"{prefix}_{hashlib.md5(f'{data}:{timestamp}'.encode()).hexdigest()[:10]}"
    
    def add_rule(self, rule: MonitorRule) -> str:
        """Add a monitoring rule"""
        self.rules.put(rule.rule_id, rule)
        
        # Index keywords in Trie
        for keyword in rule.keywords:
            kw_lower = keyword.lower() if not rule.case_sensitive else keyword
            self.keyword_trie.insert(kw_lower)
            
            # Map keyword to rule
            existing = self.keyword_rules.get(kw_lower)
            if existing:
                existing.append(rule.rule_id)
            else:
                self.keyword_rules.put(kw_lower, [rule.rule_id])
        
        self.stats["rules_count"] += 1
        return rule.rule_id
    
    def create_rule(
        self,
        name: str,
        keywords: List[str],
        severity: MatchSeverity = MatchSeverity.MEDIUM,
        **kwargs
    ) -> MonitorRule:
        """Create and add a new rule"""
        rule_id = self._generate_id("rule", name)
        rule = MonitorRule(
            rule_id=rule_id,
            name=name,
            keywords=keywords,
            severity=severity,
            **kwargs
        )
        self.add_rule(rule)
        return rule
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a monitoring rule"""
        rule = self.rules.get(rule_id)
        if not rule:
            return False
        
        # Remove from keyword mapping
        for keyword in rule.keywords:
            kw_lower = keyword.lower() if not rule.case_sensitive else keyword
            rule_list = self.keyword_rules.get(kw_lower)
            if rule_list and rule_id in rule_list:
                rule_list.remove(rule_id)
        
        self.rules.remove(rule_id)
        self.stats["rules_count"] -= 1
        return True
    
    def _check_rule(
        self,
        rule: MonitorRule,
        content: str,
        source_type: SourceType
    ) -> Optional[Dict[str, Any]]:
        """Check if content matches a rule"""
        if not rule.enabled:
            return None
        
        # Check source filter
        if rule.source_filter and source_type not in rule.source_filter:
            return None
        
        content_check = content if rule.case_sensitive else content.lower()
        
        # Check exclude keywords first
        for exclude in rule.exclude_keywords:
            exclude_check = exclude if rule.case_sensitive else exclude.lower()
            if exclude_check in content_check:
                return None
        
        matched_keywords = []
        matched_patterns = []
        
        # Check keywords
        for keyword in rule.keywords:
            kw_check = keyword if rule.case_sensitive else keyword.lower()
            if kw_check in content_check:
                matched_keywords.append(keyword)
        
        # Check regex patterns
        for pattern in rule.regex_patterns:
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            if re.search(pattern, content, flags):
                matched_patterns.append(pattern)
        
        # Check if match criteria met
        if rule.require_all:
            if len(matched_keywords) < len(rule.keywords):
                return None
        else:
            if not matched_keywords and not matched_patterns:
                return None
        
        return {
            "matched_keywords": matched_keywords,
            "matched_patterns": matched_patterns
        }
    
    def _calculate_score(
        self,
        rule: MonitorRule,
        matched_keywords: List[str],
        matched_patterns: List[str],
        source_type: SourceType
    ) -> float:
        """Calculate match score"""
        base_score = rule.severity.value * 20  # 20-100 based on severity
        
        # Bonus for multiple matches
        keyword_bonus = len(matched_keywords) * 5
        pattern_bonus = len(matched_patterns) * 10
        
        # Source type multiplier
        source_multipliers = {
            SourceType.DARK_WEB: 1.5,
            SourceType.BREACH_DB: 1.4,
            SourceType.PASTE_SITE: 1.2,
            SourceType.FORUM: 1.1,
            SourceType.CODE_REPO: 1.0,
            SourceType.SOCIAL_MEDIA: 0.9,
            SourceType.NEWS: 0.8
        }
        source_mult = source_multipliers.get(source_type, 1.0)
        
        score = (base_score + keyword_bonus + pattern_bonus) * source_mult * rule.score_multiplier
        return min(score, 100.0)  # Cap at 100
    
    def _get_snippet(self, content: str, keyword: str, context_size: int = 100) -> str:
        """Extract content snippet around matched keyword"""
        content_lower = content.lower()
        keyword_lower = keyword.lower()
        
        pos = content_lower.find(keyword_lower)
        if pos == -1:
            return content[:200]
        
        start = max(0, pos - context_size)
        end = min(len(content), pos + len(keyword) + context_size)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def scan_content(
        self,
        content: str,
        source_url: str,
        source_type: SourceType,
        metadata: Dict[str, Any] = None
    ) -> List[KeywordMatch]:
        """
        Scan content against all rules
        
        Args:
            content: Text content to scan
            source_url: URL where content was found
            source_type: Type of source
            metadata: Additional metadata
            
        Returns:
            List of keyword matches found
        """
        self.stats["content_scanned"] += 1
        matches = []
        
        # Check each rule
        for rule_id in self.rules.keys():
            rule = self.rules.get(rule_id)
            if not rule:
                continue
            
            match_result = self._check_rule(rule, content, source_type)
            if not match_result:
                continue
            
            matched_keywords = match_result["matched_keywords"]
            matched_patterns = match_result["matched_patterns"]
            
            # Calculate score
            score = self._calculate_score(
                rule, matched_keywords, matched_patterns, source_type
            )
            
            # Get content snippet
            first_keyword = matched_keywords[0] if matched_keywords else ""
            snippet = self._get_snippet(content, first_keyword) if first_keyword else content[:200]
            
            # Create match
            match_id = self._generate_id("match", f"{rule_id}:{source_url}")
            match = KeywordMatch(
                match_id=match_id,
                rule_id=rule_id,
                rule_name=rule.name,
                matched_keywords=matched_keywords,
                matched_patterns=matched_patterns,
                content_snippet=snippet,
                source_url=source_url,
                source_type=source_type,
                severity=rule.severity,
                score=score,
                discovered_at=datetime.now(),
                metadata=metadata or {}
            )
            
            # Store match
            self.matches.put(match_id, match)
            self.match_history.append(match.to_dict())
            matches.append(match)
            self.stats["total_matches"] += 1
            
            # Generate alert for high-severity matches
            if rule.severity in [MatchSeverity.CRITICAL, MatchSeverity.HIGH]:
                self._create_alert(match)
        
        return matches
    
    def _create_alert(self, match: KeywordMatch):
        """Create an alert from a match"""
        alert_id = self._generate_id("alert", match.match_id)
        
        alert = Alert(
            alert_id=alert_id,
            match_id=match.match_id,
            title=f"[{match.severity.name}] {match.rule_name}",
            description=f"Keywords matched: {', '.join(match.matched_keywords[:5])}. "
                       f"Source: {match.source_type.value}",
            severity=match.severity,
            score=match.score,
            created_at=datetime.now()
        )
        
        self.alerts.put(alert_id, alert)
        self.alert_queue.push(alert)
        self.stats["total_alerts"] += 1
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass
    
    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """Register a callback for new alerts"""
        self.alert_callbacks.append(callback)
    
    def get_pending_alerts(self, limit: int = 10) -> List[Alert]:
        """Get highest priority pending alerts"""
        alerts = []
        temp = []
        
        while not self.alert_queue.is_empty() and len(alerts) < limit:
            alert = self.alert_queue.pop()
            if not alert.acknowledged:
                alerts.append(alert)
            temp.append(alert)
        
        # Put back
        for alert in temp:
            self.alert_queue.push(alert)
        
        return alerts
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return False
        
        alert.acknowledged = True
        alert.acknowledged_by = user
        alert.acknowledged_at = datetime.now()
        return True
    
    def get_matches(
        self,
        rule_id: Optional[str] = None,
        severity: Optional[MatchSeverity] = None,
        source_type: Optional[SourceType] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[KeywordMatch]:
        """Get matches with optional filtering"""
        results = []
        
        for match_id in self.matches.keys():
            match = self.matches.get(match_id)
            if not match:
                continue
            
            if rule_id and match.rule_id != rule_id:
                continue
            if severity and match.severity != severity:
                continue
            if source_type and match.source_type != source_type:
                continue
            if since and match.discovered_at < since:
                continue
            
            results.append(match)
        
        # Sort by score descending
        results.sort(key=lambda m: m.score, reverse=True)
        return results[:limit]
    
    def get_match_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get match trends over time"""
        cutoff = datetime.now() - timedelta(days=days)
        
        daily_counts = {}
        severity_counts = {s.name: 0 for s in MatchSeverity}
        source_counts = {s.value: 0 for s in SourceType}
        rule_counts = {}
        
        for match_id in self.matches.keys():
            match = self.matches.get(match_id)
            if not match or match.discovered_at < cutoff:
                continue
            
            # Daily counts
            day_key = match.discovered_at.strftime("%Y-%m-%d")
            daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
            
            # Severity counts
            severity_counts[match.severity.name] += 1
            
            # Source counts
            source_counts[match.source_type.value] += 1
            
            # Rule counts
            rule_counts[match.rule_name] = rule_counts.get(match.rule_name, 0) + 1
        
        return {
            "period_days": days,
            "total_matches": sum(daily_counts.values()),
            "daily_counts": daily_counts,
            "by_severity": severity_counts,
            "by_source": source_counts,
            "by_rule": rule_counts,
            "top_rules": sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        }
    
    def search_keywords(self, prefix: str) -> List[str]:
        """Search keywords by prefix using Trie"""
        return self.keyword_trie.starts_with(prefix.lower())
    
    def get_rules(self, enabled_only: bool = True) -> List[MonitorRule]:
        """Get all rules"""
        rules = []
        for rule_id in self.rules.keys():
            rule = self.rules.get(rule_id)
            if rule and (not enabled_only or rule.enabled):
                rules.append(rule)
        return rules
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics"""
        return {
            **self.stats,
            "pending_alerts": len([1 for aid in self.alerts.keys() 
                                   if self.alerts.get(aid) and not self.alerts.get(aid).acknowledged]),
            "trie_word_count": self.keyword_trie.word_count(),
            "history_length": self.match_history.size
        }
    
    def export_rules(self) -> str:
        """Export all rules as JSON"""
        rules = [self.rules.get(rid).to_dict() for rid in self.rules.keys() if self.rules.get(rid)]
        return json.dumps(rules, indent=2)
    
    def import_rules(self, rules_json: str) -> int:
        """Import rules from JSON"""
        rules_data = json.loads(rules_json)
        count = 0
        
        for data in rules_data:
            rule = MonitorRule(
                rule_id=data["rule_id"],
                name=data["name"],
                keywords=data["keywords"],
                regex_patterns=data.get("regex_patterns", []),
                severity=MatchSeverity[data.get("severity", "MEDIUM")],
                enabled=data.get("enabled", True),
                case_sensitive=data.get("case_sensitive", False),
                require_all=data.get("require_all", False),
                exclude_keywords=data.get("exclude_keywords", []),
                score_multiplier=data.get("score_multiplier", 1.0)
            )
            self.add_rule(rule)
            count += 1
        
        return count


if __name__ == "__main__":
    monitor = KeywordMonitor()
    
    # Create rules
    monitor.create_rule(
        name="Company Brand Monitoring",
        keywords=["MyCorp", "mycorp.com", "Our CEO Name"],
        severity=MatchSeverity.HIGH
    )
    
    monitor.create_rule(
        name="Credential Leak Detection",
        keywords=["password", "credentials", "login"],
        regex_patterns=[r'\b[A-Za-z0-9._%+-]+@mycorp\.com\b'],
        severity=MatchSeverity.CRITICAL
    )
    
    # Scan content
    test_content = """
    New leak posted! MyCorp database dump available.
    Contains user credentials and passwords.
    Sample: john.doe@mycorp.com:password123
    Contact: seller@darkmail.onion
    """
    
    matches = monitor.scan_content(
        content=test_content,
        source_url="http://leakforum.onion/post/123",
        source_type=SourceType.DARK_WEB
    )
    
    print(f"Found {len(matches)} matches:")
    for match in matches:
        print(f"  - {match.rule_name}: score={match.score:.1f}, severity={match.severity.name}")
    
    print(f"\nStatistics: {monitor.get_statistics()}")


