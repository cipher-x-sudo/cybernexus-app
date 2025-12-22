"""Threat prediction and pattern analysis engine.

This module provides password mutation prediction, domain typosquat generation,
and threat evolution analysis using pattern matching algorithms.

Note: While Trie, HashMap, and Graph are imported and initialized in __init__,
they are not actually used in any functions. All functions use standard Python
data structures (sets, lists, dicts, Counter) instead.

This module does not use custom DSA concepts from app.core.dsa in its functions.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from collections import Counter
import re

from app.core.dsa import Trie, HashMap, Graph


class Predictor:
    
    def __init__(self):
        self._password_patterns = Trie()
        self._domain_patterns = Trie()
        self._mutation_rules = self._init_mutation_rules()
        self._known_passwords = HashMap()
        self._pattern_stats = HashMap()
    
    def _init_mutation_rules(self) -> List[Dict[str, Any]]:
        """Initialize password mutation rules.
        
        DSA-USED:
        - None: This function returns a list of dictionaries, not using custom DSA structures
        
        Returns:
            List of mutation rule dictionaries
        """
        return [
            {"name": "add_number", "transform": lambda s: [s + str(i) for i in range(100)]},
            {"name": "add_year", "transform": lambda s: [s + str(y) for y in range(2020, 2026)]},
            {"name": "add_special", "transform": lambda s: [s + c for c in "!@#$%&*"]},
            {"name": "capitalize", "transform": lambda s: [s.capitalize()]},
            {"name": "uppercase", "transform": lambda s: [s.upper()]},
            {"name": "lowercase", "transform": lambda s: [s.lower()]},
            {"name": "leet", "transform": lambda s: [
                s.replace('a', '@').replace('e', '3').replace('i', '1')
                 .replace('o', '0').replace('s', '$')
            ]},
            {"name": "common_suffix", "transform": lambda s: [
                s + suffix for suffix in ['123', '1234', '12345', '!', '!!', '1!']
            ]},
        ]
    
    def predict_password_mutations(self, password: str, max_results: int = 50) -> List[str]:
        """Predict possible password mutations based on common patterns.
        
        DSA-USED:
        - None: This function uses Python set and list, not the initialized Trie/HashMap DSA structures
        
        Args:
            password: Base password to mutate
            max_results: Maximum number of mutations to return
        
        Returns:
            List of predicted password mutations
        """
        mutations = set()
        mutations.add(password)
        
        for rule in self._mutation_rules:
            try:
                new_mutations = rule["transform"](password)
                mutations.update(new_mutations)
            except:
                continue
        
        for mutation in list(mutations)[:20]:
            for rule in self._mutation_rules[:3]:
                try:
                    new_mutations = rule["transform"](mutation)
                    mutations.update(new_mutations)
                except:
                    continue
        
        return list(mutations)[:max_results]
    
    def analyze_password_pattern(self, password: str) -> Dict[str, Any]:
        """Analyze password patterns and calculate strength.
        
        DSA-USED:
        - None: This function uses Python dict and regex, not the initialized Trie/HashMap DSA structures
        
        Args:
            password: Password to analyze
        
        Returns:
            Dictionary with pattern analysis and strength metrics
        """
        analysis = {
            "length": len(password),
            "has_uppercase": bool(re.search(r'[A-Z]', password)),
            "has_lowercase": bool(re.search(r'[a-z]', password)),
            "has_digits": bool(re.search(r'\d', password)),
            "has_special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
            "patterns": []
        }
        if re.match(r'^[a-z]+\d+$', password, re.I):
            analysis["patterns"].append("word+numbers")
        if re.match(r'^[a-z]+[!@#$%]+$', password, re.I):
            analysis["patterns"].append("word+special")
        if re.search(r'(19|20)\d{2}', password):
            analysis["patterns"].append("contains_year")
        if re.search(r'(.)\1{2,}', password):
            analysis["patterns"].append("repeated_chars")
        if password.lower() == password:
            analysis["patterns"].append("all_lowercase")
        if password[0].isupper() and password[1:].islower():
            analysis["patterns"].append("title_case")
        
        strength = 0
        if analysis["length"] >= 8:
            strength += 1
        if analysis["length"] >= 12:
            strength += 1
        if analysis["has_uppercase"]:
            strength += 1
        if analysis["has_lowercase"]:
            strength += 1
        if analysis["has_digits"]:
            strength += 1
        if analysis["has_special"]:
            strength += 1
        if analysis["length"] >= 16:
            strength += 1
        
        analysis["strength"] = min(strength, 5)
        analysis["strength_label"] = ["very_weak", "weak", "fair", "good", "strong", "very_strong"][analysis["strength"]]
        
        return analysis
    
    def generate_typosquats(self, domain: str, max_results: int = 50) -> List[Dict[str, str]]:
        """Generate typosquat domain variations.
        
        DSA-USED:
        - None: This function uses Python list and set, not the initialized Trie/Graph DSA structures
        
        Args:
            domain: Domain name to generate typosquats for
            max_results: Maximum number of typosquats to return
        
        Returns:
            List of typosquat dictionaries with domain and type
        """
        typosquats = []
        
        parts = domain.rsplit('.', 1)
        if len(parts) != 2:
            return []
        
        name, tld = parts
        for i in range(len(name)):
            typo = name[:i] + name[i+1:]
            if typo:
                typosquats.append({"domain": f"{typo}.{tld}", "type": "omission"})
        
        for i in range(len(name)):
            typo = name[:i] + name[i] + name[i:]
            typosquats.append({"domain": f"{typo}.{tld}", "type": "duplication"})
        
        for i in range(len(name) - 1):
            typo = name[:i] + name[i+1] + name[i] + name[i+2:]
            typosquats.append({"domain": f"{typo}.{tld}", "type": "swap"})
        

        qwerty_adjacent = {
            'q': 'wa', 'w': 'qeas', 'e': 'wrds', 'r': 'etdf', 't': 'ryfg',
            'y': 'tugh', 'u': 'yihj', 'i': 'uojk', 'o': 'ipkl', 'p': 'ol',
            'a': 'qwsz', 's': 'awedxz', 'd': 'serfcx', 'f': 'drtgvc',
            'g': 'ftyhbv', 'h': 'gyujnb', 'j': 'huikmn', 'k': 'jiolm',
            'l': 'kop', 'z': 'asx', 'x': 'zsdc', 'c': 'xdfv', 'v': 'cfgb',
            'b': 'vghn', 'n': 'bhjm', 'm': 'njk'
        }
        
        for i, char in enumerate(name.lower()):
            if char in qwerty_adjacent:
                for adj in qwerty_adjacent[char]:
                    typo = name[:i] + adj + name[i+1:]
                    typosquats.append({"domain": f"{typo}.{tld}", "type": "adjacent_key"})
        
        homoglyphs = {
            'o': '0', '0': 'o', 'i': '1l', '1': 'il', 'l': '1i',
            'e': '3', 'a': '4@', 's': '5$', 'b': '8', 'g': '9'
        }
        
        for i, char in enumerate(name.lower()):
            if char in homoglyphs:
                for h in homoglyphs[char]:
                    typo = name[:i] + h + name[i+1:]
                    typosquats.append({"domain": f"{typo}.{tld}", "type": "homoglyph"})
        

        common_tlds = ['com', 'net', 'org', 'io', 'co', 'info', 'biz']
        for alt_tld in common_tlds:
            if alt_tld != tld:
                typosquats.append({"domain": f"{name}.{alt_tld}", "type": "tld_swap"})
        
        for i in range(1, len(name)):
            typo = name[:i] + '-' + name[i:]
            typosquats.append({"domain": f"{typo}.{tld}", "type": "hyphenation"})
        
        seen = set()
        unique = []
        for t in typosquats:
            if t["domain"] not in seen and t["domain"] != domain:
                seen.add(t["domain"])
                unique.append(t)
        
        return unique[:max_results]
    
    def predict_threat_evolution(self, threat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict threat evolution trends from historical data.
        
        DSA-USED:
        - None: This function uses Python Counter and list, not the initialized Graph/HashMap DSA structures
        
        Args:
            threat_history: List of historical threat dictionaries
        
        Returns:
            Dictionary with evolution predictions and trend analysis
        """
        if not threat_history:
            return {"prediction": "insufficient_data"}
        
        severity_trend = []
        category_counts = Counter()
        source_counts = Counter()
        
        for threat in threat_history:
            severity_trend.append(threat.get("severity", "info"))
            category_counts[threat.get("category", "unknown")] += 1
            source_counts[threat.get("source", "unknown")] += 1
        
        severity_weights = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        severity_scores = [severity_weights.get(s, 1) for s in severity_trend]
        
        if len(severity_scores) >= 3:
            recent = sum(severity_scores[-3:]) / 3
            older = sum(severity_scores[:-3]) / max(1, len(severity_scores) - 3) if len(severity_scores) > 3 else recent
            trend = "escalating" if recent > older else "stable" if recent == older else "declining"
        else:
            trend = "insufficient_data"
        
        return {
            "severity_trend": trend,
            "most_common_category": category_counts.most_common(1)[0] if category_counts else None,
            "most_common_source": source_counts.most_common(1)[0] if source_counts else None,
            "total_analyzed": len(threat_history),
            "severity_distribution": dict(Counter(severity_trend)),
            "prediction_confidence": min(len(threat_history) / 10, 1.0)
        }


