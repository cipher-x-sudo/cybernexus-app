"""
CredentialAnalyzer Collector - Credential Leak Analysis

Inspired by: RDPassSpray (https://github.com/xFreed0m/RDPassSpray)

Analyzes credential patterns, detects password spraying attempts,
and monitors for leaked credentials. Focuses on detection and
defense rather than attack capabilities.

Features:
- Credential leak analysis
- Password spray detection
- Login pattern analysis
- Weak password identification
- Credential exposure monitoring
- Risk scoring for credentials

DSA Usage:
- Graph: User-credential relationship mapping
- AVL Tree: Sorted credential storage
- Trie: Username/password pattern matching
- HashMap: Fast credential lookups
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import re
from collections import defaultdict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dsa.graph import Graph
from core.dsa.avl_tree import AVLTree
from core.dsa.trie import Trie
from core.dsa.hashmap import HashMap


class CredentialRisk(Enum):
    """Risk levels for credentials"""
    CRITICAL = "critical"  # Known compromised
    HIGH = "high"          # Weak or exposed
    MEDIUM = "medium"      # Potentially at risk
    LOW = "low"            # Minor concerns
    SAFE = "safe"          # No known issues


class LeakSource(Enum):
    """Sources of credential leaks"""
    BREACH_DATABASE = "breach_database"
    DARK_WEB = "dark_web"
    PASTE_SITE = "paste_site"
    PHISHING = "phishing"
    MALWARE = "malware"
    INSIDER = "insider"
    UNKNOWN = "unknown"


@dataclass
class Credential:
    """Represents a credential pair"""
    credential_id: str
    username: str
    password_hash: str  # Never store plaintext
    domain: Optional[str] = None
    email: Optional[str] = None
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    leak_sources: List[LeakSource] = field(default_factory=list)
    breach_names: List[str] = field(default_factory=list)
    risk_level: CredentialRisk = CredentialRisk.MEDIUM
    risk_score: float = 0.0
    password_strength: float = 0.0
    is_reused: bool = False
    reuse_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "credential_id": self.credential_id,
            "username": self.username,
            "domain": self.domain,
            "email": self.email,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "leak_sources": [s.value for s in self.leak_sources],
            "breach_names": self.breach_names,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "password_strength": self.password_strength,
            "is_reused": self.is_reused,
            "reuse_count": self.reuse_count
        }


@dataclass
class LoginAttempt:
    """Represents a login attempt for spray detection"""
    attempt_id: str
    username: str
    target_service: str
    source_ip: str
    timestamp: datetime
    success: bool
    password_hash: str
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "attempt_id": self.attempt_id,
            "username": self.username,
            "target_service": self.target_service,
            "source_ip": self.source_ip,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success
        }


@dataclass
class SprayAttack:
    """Detected password spray attack"""
    attack_id: str
    detected_at: datetime
    source_ips: List[str]
    target_users: List[str]
    target_service: str
    attempt_count: int
    unique_passwords: int
    time_window_minutes: int
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            "attack_id": self.attack_id,
            "detected_at": self.detected_at.isoformat(),
            "source_ips": self.source_ips,
            "target_users_count": len(self.target_users),
            "target_service": self.target_service,
            "attempt_count": self.attempt_count,
            "unique_passwords": self.unique_passwords,
            "time_window_minutes": self.time_window_minutes,
            "confidence": self.confidence
        }


class CredentialAnalyzer:
    """
    Credential Leak Analysis Collector
    
    Analyzes credentials for exposure, weakness, and attack patterns.
    Inspired by RDPassSpray's understanding of credential attacks.
    """
    
    # Common weak passwords to check against
    WEAK_PASSWORDS = [
        "password", "123456", "12345678", "qwerty", "abc123",
        "password1", "password123", "admin", "letmein", "welcome",
        "monkey", "dragon", "master", "login", "princess",
        "qwerty123", "solo", "passw0rd", "starwars", "1234567890"
    ]
    
    # Password patterns indicating weakness
    WEAK_PATTERNS = [
        r'^[a-z]+$',           # Only lowercase
        r'^[A-Z]+$',           # Only uppercase
        r'^\d+$',              # Only numbers
        r'^(.)\1+$',           # Repeated character
        r'^(12|qwe|abc)',      # Common sequences
        r'(password|pass|pwd)',# Contains password
        r'(admin|root|user)',  # Contains admin terms
    ]
    
    def __init__(self):
        # Graph for credential relationships
        self.credential_graph = Graph(directed=False)
        
        # AVL Tree for sorted credential storage (by risk score)
        self.credentials_by_risk = AVLTree()
        
        # Trie for username pattern matching
        self.username_trie = Trie()
        self.password_pattern_trie = Trie()
        
        # HashMaps for lookups
        self.credentials = HashMap()  # credential_id -> Credential
        self.by_username = HashMap()  # username -> List[credential_id]
        self.by_password_hash = HashMap()  # hash -> List[credential_id]
        self.by_domain = HashMap()  # domain -> List[credential_id]
        
        # Login attempt tracking for spray detection
        self.login_attempts = HashMap()  # attempt_id -> LoginAttempt
        self.attempts_by_ip = HashMap()  # ip -> List[LoginAttempt]
        self.attempts_by_service = HashMap()  # service -> List[LoginAttempt]
        
        # Detected attacks
        self.spray_attacks = HashMap()  # attack_id -> SprayAttack
        
        # Statistics
        self.stats = {
            "credentials_analyzed": 0,
            "weak_passwords_found": 0,
            "reused_passwords": 0,
            "spray_attacks_detected": 0,
            "login_attempts_tracked": 0
        }
        
        # Build weak password trie
        for pwd in self.WEAK_PASSWORDS:
            self.password_pattern_trie.insert(pwd.lower())
    
    def _generate_id(self, prefix: str, data: str) -> str:
        """Generate unique ID"""
        ts = datetime.now().isoformat()
        return f"{prefix}_{hashlib.md5(f'{data}:{ts}'.encode()).hexdigest()[:10]}"
    
    def _hash_password(self, password: str) -> str:
        """Hash password for storage (never store plaintext)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _check_password_strength(self, password: str) -> Tuple[float, List[str]]:
        """
        Analyze password strength
        
        Returns: (strength_score 0-1, list of weaknesses)
        """
        weaknesses = []
        score = 1.0
        
        # Length check
        if len(password) < 8:
            weaknesses.append("Too short (< 8 chars)")
            score -= 0.3
        elif len(password) < 12:
            weaknesses.append("Could be longer")
            score -= 0.1
        
        # Character variety
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        variety = sum([has_lower, has_upper, has_digit, has_special])
        if variety < 2:
            weaknesses.append("Low character variety")
            score -= 0.3
        elif variety < 3:
            score -= 0.1
        
        # Check weak patterns
        for pattern in self.WEAK_PATTERNS:
            if re.search(pattern, password, re.IGNORECASE):
                weaknesses.append(f"Matches weak pattern")
                score -= 0.2
                break
        
        # Check against common passwords
        if password.lower() in self.WEAK_PASSWORDS:
            weaknesses.append("Common password")
            score -= 0.4
        
        return max(0.0, score), weaknesses
    
    def analyze_credential(
        self,
        username: str,
        password: str,
        domain: Optional[str] = None,
        email: Optional[str] = None,
        source: LeakSource = LeakSource.UNKNOWN,
        breach_name: Optional[str] = None
    ) -> Credential:
        """
        Analyze a credential for risk and weakness
        
        Args:
            username: Username
            password: Password (will be hashed)
            domain: Associated domain
            email: Associated email
            source: Where the credential was found
            breach_name: Name of the breach if applicable
            
        Returns:
            Analyzed Credential object
        """
        password_hash = self._hash_password(password)
        credential_id = self._generate_id("cred", f"{username}:{password_hash}")
        
        # Check password strength
        strength, weaknesses = self._check_password_strength(password)
        
        # Check for reuse
        existing = self.by_password_hash.get(password_hash)
        is_reused = existing is not None and len(existing) > 0
        reuse_count = len(existing) if existing else 0
        
        # Calculate risk
        risk_score, risk_level = self._calculate_risk(
            strength, is_reused, reuse_count, source
        )
        
        # Create credential
        cred = Credential(
            credential_id=credential_id,
            username=username,
            password_hash=password_hash,
            domain=domain,
            email=email,
            leak_sources=[source],
            breach_names=[breach_name] if breach_name else [],
            risk_level=risk_level,
            risk_score=risk_score,
            password_strength=strength,
            is_reused=is_reused,
            reuse_count=reuse_count
        )
        
        # Store credential
        self.credentials.put(credential_id, cred)
        
        # Index by username
        self.username_trie.insert(username.lower())
        existing_by_user = self.by_username.get(username.lower())
        if existing_by_user:
            existing_by_user.append(credential_id)
        else:
            self.by_username.put(username.lower(), [credential_id])
        
        # Index by password hash
        existing_by_pwd = self.by_password_hash.get(password_hash)
        if existing_by_pwd:
            existing_by_pwd.append(credential_id)
            # Update reuse count for all with same password
            for cid in existing_by_pwd:
                c = self.credentials.get(cid)
                if c:
                    c.is_reused = True
                    c.reuse_count = len(existing_by_pwd)
        else:
            self.by_password_hash.put(password_hash, [credential_id])
        
        # Index by domain
        if domain:
            existing_by_domain = self.by_domain.get(domain.lower())
            if existing_by_domain:
                existing_by_domain.append(credential_id)
            else:
                self.by_domain.put(domain.lower(), [credential_id])
        
        # Add to graph
        self.credential_graph.add_vertex(credential_id, {
            "type": "credential",
            "username": username,
            "risk": risk_level.value
        })
        
        if domain:
            if not self.credential_graph.has_vertex(f"domain:{domain}"):
                self.credential_graph.add_vertex(f"domain:{domain}", {"type": "domain"})
            self.credential_graph.add_edge(credential_id, f"domain:{domain}")
        
        # Add to AVL tree by risk score
        self.credentials_by_risk.insert(int(risk_score * 100), credential_id)
        
        # Update stats
        self.stats["credentials_analyzed"] += 1
        if strength < 0.5:
            self.stats["weak_passwords_found"] += 1
        if is_reused:
            self.stats["reused_passwords"] += 1
        
        return cred
    
    def _calculate_risk(
        self,
        strength: float,
        is_reused: bool,
        reuse_count: int,
        source: LeakSource
    ) -> Tuple[float, CredentialRisk]:
        """Calculate credential risk score and level"""
        score = 0.0
        
        # Weakness contribution (inverted - weaker = higher risk)
        score += (1 - strength) * 0.3
        
        # Reuse contribution
        if is_reused:
            score += min(0.3, reuse_count * 0.1)
        
        # Source contribution
        source_risk = {
            LeakSource.BREACH_DATABASE: 0.3,
            LeakSource.DARK_WEB: 0.35,
            LeakSource.MALWARE: 0.4,
            LeakSource.PHISHING: 0.35,
            LeakSource.PASTE_SITE: 0.25,
            LeakSource.INSIDER: 0.3,
            LeakSource.UNKNOWN: 0.15
        }
        score += source_risk.get(source, 0.15)
        
        # Cap at 1.0
        score = min(1.0, score)
        
        # Determine level
        if score >= 0.8:
            level = CredentialRisk.CRITICAL
        elif score >= 0.6:
            level = CredentialRisk.HIGH
        elif score >= 0.4:
            level = CredentialRisk.MEDIUM
        elif score >= 0.2:
            level = CredentialRisk.LOW
        else:
            level = CredentialRisk.SAFE
        
        return score, level
    
    def track_login_attempt(
        self,
        username: str,
        password: str,
        target_service: str,
        source_ip: str,
        success: bool,
        user_agent: Optional[str] = None
    ) -> Optional[SprayAttack]:
        """
        Track a login attempt and detect spray attacks
        
        Returns SprayAttack if attack detected
        """
        attempt_id = self._generate_id("attempt", f"{username}:{source_ip}")
        password_hash = self._hash_password(password)
        
        attempt = LoginAttempt(
            attempt_id=attempt_id,
            username=username,
            target_service=target_service,
            source_ip=source_ip,
            timestamp=datetime.now(),
            success=success,
            password_hash=password_hash,
            user_agent=user_agent
        )
        
        # Store attempt
        self.login_attempts.put(attempt_id, attempt)
        
        # Index by IP
        by_ip = self.attempts_by_ip.get(source_ip)
        if by_ip:
            by_ip.append(attempt)
        else:
            self.attempts_by_ip.put(source_ip, [attempt])
        
        # Index by service
        by_service = self.attempts_by_service.get(target_service)
        if by_service:
            by_service.append(attempt)
        else:
            self.attempts_by_service.put(target_service, [attempt])
        
        self.stats["login_attempts_tracked"] += 1
        
        # Check for spray attack
        return self._detect_spray_attack(target_service)
    
    def _detect_spray_attack(
        self,
        target_service: str,
        time_window_minutes: int = 30,
        min_users: int = 10,
        min_attempts: int = 20
    ) -> Optional[SprayAttack]:
        """
        Detect password spray attack patterns
        
        Indicators:
        - Many users targeted
        - Few unique passwords
        - Short time window
        - Multiple source IPs or single IP
        """
        attempts = self.attempts_by_service.get(target_service)
        if not attempts:
            return None
        
        cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
        recent = [a for a in attempts if a.timestamp >= cutoff]
        
        if len(recent) < min_attempts:
            return None
        
        # Analyze patterns
        unique_users = set(a.username for a in recent)
        unique_passwords = set(a.password_hash for a in recent)
        unique_ips = set(a.source_ip for a in recent)
        
        if len(unique_users) < min_users:
            return None
        
        # Spray indicator: many users, few passwords
        user_to_password_ratio = len(unique_users) / max(len(unique_passwords), 1)
        
        if user_to_password_ratio < 3:  # Less than 3 users per password = not spray
            return None
        
        # Calculate confidence
        confidence = min(1.0, (user_to_password_ratio - 3) / 10 + 0.5)
        
        attack_id = self._generate_id("spray", target_service)
        attack = SprayAttack(
            attack_id=attack_id,
            detected_at=datetime.now(),
            source_ips=list(unique_ips),
            target_users=list(unique_users),
            target_service=target_service,
            attempt_count=len(recent),
            unique_passwords=len(unique_passwords),
            time_window_minutes=time_window_minutes,
            confidence=confidence
        )
        
        self.spray_attacks.put(attack_id, attack)
        self.stats["spray_attacks_detected"] += 1
        
        return attack
    
    def check_credential_exposure(
        self,
        username: str,
        email: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[Credential]:
        """Check if credentials are exposed in known breaches"""
        results = []
        
        # Check by username
        by_user = self.by_username.get(username.lower())
        if by_user:
            for cid in by_user:
                cred = self.credentials.get(cid)
                if cred:
                    results.append(cred)
        
        # Check by domain
        if domain:
            by_domain = self.by_domain.get(domain.lower())
            if by_domain:
                for cid in by_domain:
                    cred = self.credentials.get(cid)
                    if cred and cred not in results:
                        # Check if username matches
                        if cred.username.lower() == username.lower():
                            results.append(cred)
        
        return sorted(results, key=lambda c: c.risk_score, reverse=True)
    
    def find_reused_passwords(self, min_reuse: int = 2) -> List[Dict[str, Any]]:
        """Find passwords reused across multiple accounts"""
        reused = []
        
        for pwd_hash in self.by_password_hash.keys():
            cred_ids = self.by_password_hash.get(pwd_hash)
            if cred_ids and len(cred_ids) >= min_reuse:
                creds = [self.credentials.get(cid) for cid in cred_ids if self.credentials.get(cid)]
                if creds:
                    reused.append({
                        "password_hash": pwd_hash[:16] + "...",
                        "reuse_count": len(creds),
                        "usernames": [c.username for c in creds],
                        "domains": list(set(c.domain for c in creds if c.domain)),
                        "max_risk": max(c.risk_score for c in creds)
                    })
        
        return sorted(reused, key=lambda r: r["reuse_count"], reverse=True)
    
    def search_usernames(self, prefix: str) -> List[str]:
        """Search usernames by prefix"""
        return self.username_trie.starts_with(prefix.lower())
    
    def get_high_risk_credentials(self, limit: int = 20) -> List[Credential]:
        """Get credentials with highest risk"""
        results = []
        
        for cid in self.credentials.keys():
            cred = self.credentials.get(cid)
            if cred:
                results.append(cred)
        
        return sorted(results, key=lambda c: c.risk_score, reverse=True)[:limit]
    
    def get_domain_exposure(self, domain: str) -> Dict[str, Any]:
        """Get exposure summary for a domain"""
        cred_ids = self.by_domain.get(domain.lower())
        if not cred_ids:
            return {"domain": domain, "exposure_count": 0}
        
        creds = [self.credentials.get(cid) for cid in cred_ids if self.credentials.get(cid)]
        
        return {
            "domain": domain,
            "exposure_count": len(creds),
            "risk_distribution": {
                level.value: len([c for c in creds if c.risk_level == level])
                for level in CredentialRisk
            },
            "average_risk": sum(c.risk_score for c in creds) / len(creds) if creds else 0,
            "weak_passwords": len([c for c in creds if c.password_strength < 0.5]),
            "reused_passwords": len([c for c in creds if c.is_reused]),
            "breach_sources": list(set(
                source.value 
                for c in creds 
                for source in c.leak_sources
            ))
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics"""
        return {
            **self.stats,
            "unique_usernames": self.username_trie.word_count(),
            "unique_password_hashes": len(list(self.by_password_hash.keys())),
            "domains_tracked": len(list(self.by_domain.keys())),
            "graph_vertices": self.credential_graph.vertex_count(),
            "graph_edges": self.credential_graph.edge_count()
        }


if __name__ == "__main__":
    analyzer = CredentialAnalyzer()
    
    # Analyze some credentials
    cred1 = analyzer.analyze_credential(
        username="john.doe",
        password="password123",
        domain="example.com",
        source=LeakSource.BREACH_DATABASE,
        breach_name="ExampleBreach2024"
    )
    print(f"Credential 1: {cred1.username} - Risk: {cred1.risk_level.value} ({cred1.risk_score:.2f})")
    
    cred2 = analyzer.analyze_credential(
        username="jane.smith",
        password="password123",  # Same password - reuse!
        domain="example.com",
        source=LeakSource.DARK_WEB
    )
    print(f"Credential 2: {cred2.username} - Risk: {cred2.risk_level.value} ({cred2.risk_score:.2f})")
    print(f"  Reused: {cred2.is_reused}, Count: {cred2.reuse_count}")
    
    # Check reused passwords
    reused = analyzer.find_reused_passwords()
    print(f"\nReused passwords: {len(reused)}")
    
    print(f"\nStatistics: {analyzer.get_statistics()}")


