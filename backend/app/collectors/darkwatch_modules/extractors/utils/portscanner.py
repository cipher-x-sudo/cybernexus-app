"""
Port Scanner Utility

Scans for open ports on onion services.
Simplified version adapted from freshonions-torscraper.
"""

import socket
import logging
from typing import List, Dict, Optional
from app.config import settings


PORTS = {
    8333: "bitcoin",
    9051: "bitcoin-control",
    9333: "litecoin",
    22556: "dogecoin",
    6697: "irc",
    6667: "irc",
    143: "imap",
    110: "pop3",
    119: "nntp",
    22: "ssh",
    2222: "ssh?",
    23: "telnet",
    25: "smtp",
    80: "http",
    443: "https",
    21: "ftp",
    5900: "vnc",
    27017: "mongodb",
    9200: "elasticsearch",
    3128: "squid-proxy?",
    8080: "proxy?",
    8118: "proxy?",
    8000: "proxy?",
    9878: "richochet",
}


def get_service_name(port: int) -> Optional[str]:
    """
    Get service name for a port.
    
    Args:
        port: Port number
        
    Returns:
        Service name or None
    """
    return PORTS.get(port)


def scan_ports(host: str, ports: Optional[List[int]] = None, timeout: float = 2.0) -> List[Dict]:
    """
    Scan for open ports on a host.
    
    Args:
        host: Hostname or IP address
        ports: List of ports to scan (defaults to common ports)
        timeout: Connection timeout in seconds
        
    Returns:
        List of dictionaries with port and service info
    """
    logger = logging.getLogger(__name__)
    
    if ports is None:
        ports = list(PORTS.keys())
    
    open_ports = []
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                service = get_service_name(port)
                open_ports.append({
                    "port": port,
                    "service": service,
                    "status": "open"
                })
                logger.debug(f"Port {port} ({service}) is open on {host}")
        
        except socket.gaierror:
            logger.debug(f"Hostname resolution failed for {host}")
            break
        except Exception as e:
            logger.debug(f"Error scanning port {port} on {host}: {e}")
            continue
    
    return open_ports
