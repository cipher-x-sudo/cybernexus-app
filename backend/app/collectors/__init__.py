"""
CyberNexus Collectors

Data ingestion modules inspired by various security tools.

Tool Mapping:
- WebRecon         <- oxdork (Google dorking)
- DomainTree       <- lookyloo (Domain tree capture)
- ConfigAudit      <- nginxpwner (Misconfig scanning)
- EmailAudit       <- espoofer (Email security testing)
- DarkWatch        <- freshonions (Tor crawling)
- KeywordMonitor   <- VigilantOnion (Keyword monitoring)
- TunnelDetector   <- Tunna (Tunnel detection)
- TrainingKB       <- awesome-social-engineering (Training content)
"""

from .web_recon import WebRecon
from .config_audit import ConfigAudit
from .email_audit import EmailAudit
from .domain_tree import DomainTree
from .dark_watch import DarkWatch
from .keyword_monitor import KeywordMonitor
from .tunnel_detector import TunnelDetector
from .training_kb import TrainingKB

__all__ = [
    "WebRecon",
    "ConfigAudit", 
    "EmailAudit",
    "DomainTree",
    "DarkWatch",
    "KeywordMonitor",
    "TunnelDetector",
    "TrainingKB"
]
