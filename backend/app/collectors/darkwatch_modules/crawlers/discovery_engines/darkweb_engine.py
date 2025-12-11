#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Dark Web Discovery Engine

Discovers .onion URLs from DiscoverDarkWeb service.
"""

import requests
import time
from bs4 import BeautifulSoup
from typing import List, Optional
from loguru import logger
from app.config import settings


class DarkWebEngine:
    """Engine for discovering URLs from DiscoverDarkWeb service."""
    
    def __init__(
        self,
        proxy_host: Optional[str] = None,
        proxy_port: Optional[int] = None,
        proxy_type: Optional[str] = None
    ):
        """
        Initialize DarkWeb engine.
        
        Args:
            proxy_host: Tor proxy host (defaults to settings)
            proxy_port: Tor proxy port (defaults to settings)
            proxy_type: Proxy type (defaults to settings)
        """
        self.session = requests.session()
        
        self.proxy_host = proxy_host or settings.TOR_PROXY_HOST
        self.proxy_port = proxy_port or settings.TOR_PROXY_PORT
        self.proxy_type = proxy_type or settings.TOR_PROXY_TYPE
        
        self.proxies = {
            "http": f"{self.proxy_type}://{self.proxy_host}:{self.proxy_port}",
        }
        
        logger.info(f"[DarkWebEngine] Initialized with proxy={self.proxy_type}://{self.proxy_host}:{self.proxy_port}")
    
    def discover_urls(self) -> List[str]:
        """
        Discover .onion URLs from DiscoverDarkWeb service.
        
        Returns:
            List of discovered .onion URLs
        """
        url = 'http://3bbaaaccczcbdddz.onion/discover'
        logger.info(f'[DarkWebEngine] Connecting to {url} via proxy')
        onionurls = []
        discovery_start = time.time()
        
        try:
            logger.debug(f'[DarkWebEngine] Making GET request to {url}')
            request = self.session.get(
                url,
                proxies=self.proxies,
                timeout=100
            )
            request_time = time.time() - discovery_start
            logger.info(f'[DarkWebEngine] Request to {url} completed in {request_time:.2f}s, status={request.status_code}')
            
            if request.status_code == 200:
                logger.debug(f'[DarkWebEngine] Parsing HTML response')
                parse_start = time.time()
                soup = BeautifulSoup(request.content, features="lxml")
                table = soup.find('table', {'class': 'table'})
                parse_time = time.time() - parse_start
                logger.info(f'[DarkWebEngine] HTML parsing completed in {parse_time:.3f}s')
                
                if table:
                    logger.debug(f'[DarkWebEngine] Extracting URLs from table')
                    for raw in table.findAll('a'):
                        if 'href' in raw.attrs:
                            href = raw['href']
                            if '/search?q=' in href:
                                onionurl = href.replace('/search?q=', '')
                                onionurls.append(onionurl)
                    logger.info(f'[DarkWebEngine] Extracted {len(onionurls)} URLs from table')
                else:
                    logger.warning(f'[DarkWebEngine] No table found in response from {url}')
            else:
                logger.warning(f'[DarkWebEngine] Request to {url} returned status {request.status_code}')
            
            total_time = time.time() - discovery_start
            logger.info(f'[DarkWebEngine] Discovered {len(onionurls)} URLs from DiscoverDarkWeb in {total_time:.2f}s')
            return list(set(onionurls))  # Return unique URLs
        
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.InvalidURL) as e:
            error_time = time.time() - discovery_start
            logger.error(
                f'[DarkWebEngine] Unable to connect to DiscoverDarkWeb service after {error_time:.2f}s: {e}'
            )
            return []
        
        except Exception as e:
            error_time = time.time() - discovery_start
            logger.error(f"[DarkWebEngine] Error after {error_time:.2f}s: {e}", exc_info=True)
            return []
