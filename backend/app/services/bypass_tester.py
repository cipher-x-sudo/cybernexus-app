"""
Email Security Bypass Tester

Inspired by: espoofer
Purpose: Analyze email configurations for potential SPF/DKIM/DMARC bypass vulnerabilities.
Note: This performs analysis only, does not send actual spoofing emails.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger


class BypassTester:
    """
    Email Security Bypass Tester.
    
    Analyzes email configurations for potential bypass vulnerabilities
    based on known attack patterns from espoofer research.
    """
    
    def __init__(self):
        """Initialize Bypass Tester."""
        pass
    
    async def analyze_bypass_vulnerabilities(
        self, 
        domain: str,
        email_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze email configuration for bypass vulnerabilities.
        
        Args:
            domain: Target domain
            email_config: Email security configuration from EmailAudit
            
        Returns:
            Bypass analysis results
        """
        logger.info(f"Analyzing bypass vulnerabilities for {domain}")
        
        results = {
            "domain": domain,
            "timestamp": datetime.utcnow().isoformat(),
            "vulnerabilities": [],
            "risk_level": "low",
            "bypass_scenarios": []
        }
        
        # Analyze SPF bypass vulnerabilities
        spf_vulns = self._analyze_spf_bypasses(email_config.get("spf", {}))
        results["vulnerabilities"].extend(spf_vulns)
        
        # Analyze DKIM bypass vulnerabilities
        dkim_vulns = self._analyze_dkim_bypasses(email_config.get("dkim", {}))
        results["vulnerabilities"].extend(dkim_vulns)
        
        # Analyze DMARC bypass vulnerabilities
        dmarc_vulns = self._analyze_dmarc_bypasses(email_config.get("dmarc", {}))
        results["vulnerabilities"].extend(dmarc_vulns)
        
        # Analyze composition attacks (SPF + DKIM + DMARC interaction)
        composition_vulns = self._analyze_composition_attacks(email_config)
        results["vulnerabilities"].extend(composition_vulns)
        
        # Calculate overall risk level
        if results["vulnerabilities"]:
            critical_count = sum(1 for v in results["vulnerabilities"] if v.get("severity") == "critical")
            high_count = sum(1 for v in results["vulnerabilities"] if v.get("severity") == "high")
            
            if critical_count > 0:
                results["risk_level"] = "critical"
            elif high_count > 0:
                results["risk_level"] = "high"
            elif len(results["vulnerabilities"]) > 3:
                results["risk_level"] = "medium"
            else:
                results["risk_level"] = "low"
        
        # Generate bypass scenarios
        results["bypass_scenarios"] = self._generate_bypass_scenarios(results["vulnerabilities"])
        
        return results
    
    def _analyze_spf_bypasses(self, spf_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze SPF configuration for bypass vulnerabilities.
        
        Based on espoofer test cases:
        - A1: Non-existent subdomains in MAIL FROM
        - A2: Empty MAIL FROM addresses
        - A3: NUL ambiguity
        - A4: SPF include chain issues
        """
        vulnerabilities = []
        
        if not spf_config.get("exists"):
            vulnerabilities.append({
                "severity": "critical",
                "type": "spf_bypass",
                "test_case": "A1",
                "title": "No SPF Record - Vulnerable to Non-existent Subdomain Attack",
                "description": "Domain has no SPF record. Attackers can use non-existent subdomains in MAIL FROM to bypass SPF checks.",
                "attack_vector": "Use non-existent subdomain in MAIL FROM (e.g., <any@mailfrom.notexist.legitimate.com>)",
                "recommendation": "Create an SPF record with proper mechanisms"
            })
            return vulnerabilities
        
        # Check for +all mechanism (allows all)
        if spf_config.get("all_mechanism") == '+all':
            vulnerabilities.append({
                "severity": "critical",
                "type": "spf_bypass",
                "test_case": "SPF_ALL",
                "title": "SPF +all Mechanism - Allows All Senders",
                "description": "SPF record uses +all which allows any sender, effectively disabling SPF protection.",
                "attack_vector": "Any sender can pass SPF check",
                "recommendation": "Change +all to ~all (softfail) or -all (hardfail)"
            })
        
        # Check for missing 'all' mechanism
        if spf_config.get("all_mechanism") is None:
            vulnerabilities.append({
                "severity": "high",
                "type": "spf_bypass",
                "test_case": "SPF_NO_ALL",
                "title": "SPF Missing 'all' Mechanism",
                "description": "SPF record doesn't specify what to do with unmatched senders. Default behavior may allow spoofing.",
                "attack_vector": "Senders not matching SPF mechanisms may pass",
                "recommendation": "Add explicit 'all' mechanism (-all, ~all, or ?all)"
            })
        
        # Check for too many includes (potential for include chain issues)
        includes = spf_config.get("includes", [])
        if len(includes) > 10:
            vulnerabilities.append({
                "severity": "medium",
                "type": "spf_bypass",
                "test_case": "SPF_INCLUDE_CHAIN",
                "title": "SPF Include Chain Too Long",
                "description": "Too many SPF includes (>10) can lead to DNS lookup failures and potential bypasses.",
                "attack_vector": "Exploit DNS lookup failures in include chain",
                "recommendation": "Consolidate SPF includes, use SPF macros if possible"
            })
        
        # Check for softfail (~all) - less secure than hardfail
        if spf_config.get("all_mechanism") == '~all':
            vulnerabilities.append({
                "severity": "medium",
                "type": "spf_bypass",
                "test_case": "SPF_SOFTFAIL",
                "title": "SPF Softfail - May Allow Spoofing",
                "description": "SPF uses ~all (softfail) which may allow spoofed emails to pass in some configurations.",
                "attack_vector": "Spoofed emails may pass with softfail",
                "recommendation": "Upgrade to -all (hardfail) for better protection"
            })
        
        return vulnerabilities
    
    def _analyze_dkim_bypasses(self, dkim_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze DKIM configuration for bypass vulnerabilities.
        
        Based on espoofer test cases:
        - B1: DKIM signature on wrong header
        - B2: Multiple From headers
        - B3: From header in different case
        """
        vulnerabilities = []
        
        if not dkim_config.get("selectors_found"):
            vulnerabilities.append({
                "severity": "high",
                "type": "dkim_bypass",
                "test_case": "B1",
                "title": "No DKIM Records - Vulnerable to Header Manipulation",
                "description": "No DKIM records found. Emails cannot be cryptographically verified.",
                "attack_vector": "Manipulate From header, use multiple From headers, or use different case",
                "recommendation": "Configure DKIM signing for all outgoing emails"
            })
            return vulnerabilities
        
        # Check if only one selector found (less resilient)
        selectors = dkim_config.get("selectors_found", [])
        if len(selectors) == 1:
            vulnerabilities.append({
                "severity": "low",
                "type": "dkim_bypass",
                "test_case": "DKIM_SINGLE_SELECTOR",
                "title": "Single DKIM Selector - Limited Resilience",
                "description": "Only one DKIM selector found. Consider using multiple selectors for better resilience.",
                "attack_vector": "If selector is compromised, all emails are vulnerable",
                "recommendation": "Configure multiple DKIM selectors"
            })
        
        return vulnerabilities
    
    def _analyze_dmarc_bypasses(self, dmarc_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze DMARC configuration for bypass vulnerabilities.
        
        Based on espoofer test cases:
        - C1: DMARC policy 'none'
        - C2: DMARC percentage < 100%
        - C3: Subdomain policy issues
        """
        vulnerabilities = []
        
        if not dmarc_config.get("exists"):
            vulnerabilities.append({
                "severity": "critical",
                "type": "dmarc_bypass",
                "test_case": "C1",
                "title": "No DMARC Record - No Policy Enforcement",
                "description": "No DMARC record found. No email authentication policy is enforced.",
                "attack_vector": "Any spoofing attack can succeed",
                "recommendation": "Create a DMARC record with appropriate policy"
            })
            return vulnerabilities
        
        # Check for 'none' policy
        if dmarc_config.get("policy") == 'none':
            vulnerabilities.append({
                "severity": "high",
                "type": "dmarc_bypass",
                "test_case": "C1",
                "title": "DMARC Policy 'none' - Monitoring Only",
                "description": "DMARC policy is set to 'none', which means failed emails are still delivered. No enforcement.",
                "attack_vector": "Spoofed emails pass DMARC but are delivered anyway",
                "recommendation": "Upgrade DMARC policy to 'quarantine' or 'reject'"
            })
        
        # Check for percentage < 100%
        pct = dmarc_config.get("pct", 100)
        if pct < 100:
            vulnerabilities.append({
                "severity": "medium",
                "type": "dmarc_bypass",
                "test_case": "C2",
                "title": f"DMARC Only Applies to {pct}% of Emails",
                "description": f"DMARC policy only applies to {pct}% of emails. {100-pct}% are not protected.",
                "attack_vector": "Some emails may bypass DMARC checks",
                "recommendation": "Set DMARC pct=100 for full coverage"
            })
        
        # Check subdomain policy
        subdomain_policy = dmarc_config.get("subdomain_policy")
        if subdomain_policy == 'none' or subdomain_policy is None:
            vulnerabilities.append({
                "severity": "medium",
                "type": "dmarc_bypass",
                "test_case": "C3",
                "title": "Weak Subdomain DMARC Policy",
                "description": "Subdomain DMARC policy is 'none' or not set. Subdomains may be vulnerable to spoofing.",
                "attack_vector": "Spoof emails from subdomains",
                "recommendation": "Set explicit subdomain policy (sp=) in DMARC record"
            })
        
        return vulnerabilities
    
    def _analyze_composition_attacks(self, email_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze composition attacks (interaction between SPF, DKIM, DMARC).
        
        Based on espoofer research on composition attacks.
        """
        vulnerabilities = []
        
        spf = email_config.get("spf", {})
        dkim = email_config.get("dkim", {})
        dmarc = email_config.get("dmarc", {})
        
        # Check if SPF passes but DKIM fails (composition issue)
        if spf.get("exists") and not dkim.get("selectors_found"):
            if dmarc.get("policy") in ['quarantine', 'reject']:
                vulnerabilities.append({
                    "severity": "medium",
                    "type": "composition_attack",
                    "test_case": "COMP_SPF_DKIM",
                    "title": "SPF Passes but DKIM Missing - Composition Vulnerability",
                    "description": "SPF is configured but DKIM is missing. Some mail servers may accept emails based on SPF alone.",
                    "attack_vector": "Exploit SPF-only validation in some mail servers",
                    "recommendation": "Configure both SPF and DKIM for defense in depth"
                })
        
        # Check if DMARC is missing but SPF/DKIM exist
        if (spf.get("exists") or dkim.get("selectors_found")) and not dmarc.get("exists"):
            vulnerabilities.append({
                "severity": "high",
                "type": "composition_attack",
                "test_case": "COMP_NO_DMARC",
                "title": "SPF/DKIM Configured but No DMARC - Policy Gap",
                "description": "SPF or DKIM is configured but DMARC is missing. No unified policy enforcement.",
                "attack_vector": "Exploit gaps in authentication policy",
                "recommendation": "Add DMARC record to enforce unified email authentication policy"
            })
        
        return vulnerabilities
    
    def _generate_bypass_scenarios(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate potential bypass scenarios based on vulnerabilities.
        
        Args:
            vulnerabilities: List of identified vulnerabilities
            
        Returns:
            List of bypass scenarios
        """
        scenarios = []
        
        for vuln in vulnerabilities:
            scenario = {
                "id": vuln.get("test_case", "unknown"),
                "severity": vuln.get("severity"),
                "title": vuln.get("title"),
                "description": vuln.get("description"),
                "attack_vector": vuln.get("attack_vector"),
                "mitigation": vuln.get("recommendation"),
                "type": vuln.get("type")
            }
            scenarios.append(scenario)
        
        return scenarios







