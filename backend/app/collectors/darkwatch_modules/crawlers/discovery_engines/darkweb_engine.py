#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Dark Web Discovery Engine

Discovers .onion URLs from DiscoverDarkWeb service.
"""

import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Optional
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
        self.logger = logging.getLogger(__name__)
        self.session = requests.session()
        
        self.proxy_host = proxy_host or settings.TOR_PROXY_HOST
        self.proxy_port = proxy_port or settings.TOR_PROXY_PORT
        self.proxy_type = proxy_type or settings.TOR_PROXY_TYPE
        
        self.proxies = {
            "http": f"{self.proxy_type}://{self.proxy_host}:{self.proxy_port}",
        }
    
    def discover_urls(self) -> List[str]:
        """
        Discover .onion URLs from DiscoverDarkWeb service.
        
        Returns:
            List of discovered .onion URLs
        """
        url = 'http://3bbaaaccczcbdddz.onion/discover'
        self.logger.info(f'Connecting to {url}')
        onionurls = []
        
        try:
            request = self.session.get(
                url,
                proxies=self.proxies,
                timeout=100
            )
            
            if request.status_code == 200:
                soup = BeautifulSoup(request.content, features="lxml")
                table = soup.find('table', {'class': 'table'})
                
                if table:
                    for raw in table.findAll('a'):
                        if 'href' in raw.attrs:
                            href = raw['href']
                            if '/search?q=' in href:
                                onionurl = href.replace('/search?q=', '')
                                onionurls.append(onionurl)
            
            self.logger.info(f'Found {len(onionurls)} URLs from DiscoverDarkWeb')
            return list(set(onionurls))  # Return unique URLs
        
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.InvalidURL) as e:
            self.logger.error(
                f'Unable to connect to DiscoverDarkWeb service: {e}'
            )
            return []
        
        except Exception as e:
            self.logger.error(f"DarkWeb engine error: {e}")
            return []
