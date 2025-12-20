"""
Tor Connectivity Check Utility

Provides functionality to verify Tor proxy connectivity and status.
"""

import time
import requests
from typing import Dict, Any
from loguru import logger

from app.config import settings


def check_tor_connectivity_quick(timeout: int = 5) -> Dict[str, Any]:
    """
    Quick check of Tor connectivity with shorter timeout for health checks.
    
    This version uses a shorter timeout to avoid blocking health checks for too long.
    Use this for health check endpoints where fast response is critical.
    
    Args:
        timeout: Timeout in seconds (default: 5 seconds)
    
    Returns:
        Dictionary with Tor status information (same format as check_tor_connectivity)
    """
    proxy_host = settings.TOR_PROXY_HOST
    proxy_port = settings.TOR_PROXY_PORT
    proxy_type = settings.TOR_PROXY_TYPE
    
    # Test endpoint - official Tor Project API
    test_url = "https://check.torproject.org/api/ip"
    
    # Configure proxy (same pattern as TorConnector)
    proxies = {
        "http": f"{proxy_type}://{proxy_host}:{proxy_port}",
        "https": f"{proxy_type}://{proxy_host}:{proxy_port}",
    }
    
    result = {
        "status": "disconnected",
        "is_tor": False,
        "ip": None,
        "response_time_ms": None,
        "error": None,
        "host": proxy_host,
        "port": proxy_port,
    }
    
    try:
        logger.debug(f"Quick Tor connectivity check via {proxy_type}://{proxy_host}:{proxy_port} (timeout: {timeout}s)")
        start_time = time.time()
        
        response = requests.get(
            test_url,
            proxies=proxies,
            timeout=timeout,
            headers={
                'User-Agent': 'CyberNexus-TorHealthCheck/1.0'
            }
        )
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        result["response_time_ms"] = round(response_time, 2)
        
        if response.status_code == 200:
            data = response.json()
            result["status"] = "connected"
            result["is_tor"] = data.get("IsTor", False)
            result["ip"] = data.get("IP", None)
            
            if result["is_tor"]:
                logger.debug(
                    f"Quick Tor check: connected - Exit node IP: {result['ip']}, "
                    f"Response time: {result['response_time_ms']}ms"
                )
            else:
                logger.debug(
                    f"Quick Tor check: proxy connected but not using Tor network. "
                    f"IP: {result['ip']}, Response time: {result['response_time_ms']}ms"
                )
                result["error"] = "Proxy connected but not routing through Tor network"
        else:
            result["status"] = "error"
            result["error"] = f"Unexpected status code: {response.status_code}"
            logger.debug(f"Quick Tor check returned status {response.status_code}")
            
    except requests.exceptions.ProxyError as e:
        result["status"] = "error"
        result["error"] = f"Proxy error: {str(e)}"
        logger.debug(f"Quick Tor check proxy error: {e}")
        
    except requests.exceptions.ConnectionError as e:
        result["status"] = "error"
        result["error"] = f"Connection refused: {str(e)}"
        logger.debug(f"Quick Tor check connection refused: {e}")
        
    except requests.exceptions.Timeout as e:
        result["status"] = "error"
        result["error"] = f"Connection timeout after {timeout}s"
        logger.debug(f"Quick Tor check timeout after {timeout}s: {e}")
        
    except requests.exceptions.RequestException as e:
        result["status"] = "error"
        result["error"] = f"Request error: {str(e)}"
        logger.debug(f"Quick Tor check request error: {e}")
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Unexpected error: {str(e)}"
        logger.debug(f"Unexpected error during quick Tor check: {e}", exc_info=True)
    
    return result


def check_tor_connectivity() -> Dict[str, Any]:
    """
    Check connectivity to Tor proxy service.
    
    Makes a test request through the Tor proxy to verify it's working.
    Uses the official Tor Project API to confirm we're using a Tor exit node.
    
    Returns:
        Dictionary with:
        - status: "connected" | "disconnected" | "error"
        - is_tor: bool - Whether the response indicates we're using Tor
        - ip: Optional[str] - Exit node IP address
        - response_time_ms: Optional[float] - Request response time in milliseconds
        - error: Optional[str] - Error message if connection failed
        - host: str - Tor proxy host
        - port: int - Tor proxy port
    """
    proxy_host = settings.TOR_PROXY_HOST
    proxy_port = settings.TOR_PROXY_PORT
    proxy_type = settings.TOR_PROXY_TYPE
    timeout = settings.TOR_HEALTH_CHECK_TIMEOUT
    
    # Test endpoint - official Tor Project API
    test_url = "https://check.torproject.org/api/ip"
    
    # Configure proxy (same pattern as TorConnector)
    proxies = {
        "http": f"{proxy_type}://{proxy_host}:{proxy_port}",
        "https": f"{proxy_type}://{proxy_host}:{proxy_port}",
    }
    
    result = {
        "status": "disconnected",
        "is_tor": False,
        "ip": None,
        "response_time_ms": None,
        "error": None,
        "host": proxy_host,
        "port": proxy_port,
    }
    
    try:
        logger.debug(f"Testing Tor connectivity via {proxy_type}://{proxy_host}:{proxy_port}")
        start_time = time.time()
        
        response = requests.get(
            test_url,
            proxies=proxies,
            timeout=timeout,
            headers={
                'User-Agent': 'CyberNexus-TorHealthCheck/1.0'
            }
        )
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        result["response_time_ms"] = round(response_time, 2)
        
        if response.status_code == 200:
            data = response.json()
            result["status"] = "connected"
            result["is_tor"] = data.get("IsTor", False)
            result["ip"] = data.get("IP", None)
            
            if result["is_tor"]:
                logger.info(
                    f"Tor connectivity verified - Exit node IP: {result['ip']}, "
                    f"Response time: {result['response_time_ms']}ms"
                )
            else:
                logger.warning(
                    f"Tor proxy connected but not using Tor network. "
                    f"IP: {result['ip']}, Response time: {result['response_time_ms']}ms"
                )
                result["error"] = "Proxy connected but not routing through Tor network"
        else:
            result["status"] = "error"
            result["error"] = f"Unexpected status code: {response.status_code}"
            logger.warning(f"Tor connectivity check returned status {response.status_code}")
            
    except requests.exceptions.ProxyError as e:
        result["status"] = "error"
        result["error"] = f"Proxy error: {str(e)}"
        logger.error(f"Tor proxy connection error: {e}")
        
    except requests.exceptions.ConnectionError as e:
        result["status"] = "error"
        result["error"] = f"Connection refused: {str(e)}"
        logger.error(f"Tor proxy connection refused: {e}")
        
    except requests.exceptions.Timeout as e:
        result["status"] = "error"
        result["error"] = f"Connection timeout after {timeout}s"
        logger.error(f"Tor proxy connection timeout: {e}")
        
    except requests.exceptions.RequestException as e:
        result["status"] = "error"
        result["error"] = f"Request error: {str(e)}"
        logger.error(f"Tor connectivity check request error: {e}")
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Unexpected error: {str(e)}"
        logger.exception(f"Unexpected error during Tor connectivity check: {e}")
    
    return result
