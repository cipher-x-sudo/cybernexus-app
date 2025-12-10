#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Search Engine Discovery

Discovers .onion URLs from TORCH search engine.
"""

import requests
import logging
from random import choice
from bs4 import BeautifulSoup
from typing import List, Optional
from app.config import settings


class SearchEngine:
    """Engine for discovering URLs from TORCH search engine."""
    
    def __init__(
        self,
        proxy_host: Optional[str] = None,
        proxy_port: Optional[int] = None,
        proxy_type: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize Search engine.
        
        Args:
            proxy_host: Tor proxy host (defaults to settings)
            proxy_port: Tor proxy port (defaults to settings)
            proxy_type: Proxy type (defaults to settings)
            timeout: Request timeout (defaults to settings)
        """
        self.logger = logging.getLogger(__name__)
        self.session = requests.session()
        
        self.proxy_host = proxy_host or settings.TOR_PROXY_HOST
        self.proxy_port = proxy_port or settings.TOR_PROXY_PORT
        self.proxy_type = proxy_type or settings.TOR_PROXY_TYPE
        self.timeout = timeout or settings.TOR_TIMEOUT
        
        self.url = 'http://xmh57jrzrnw6insl.onion'
        self.desktop_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0'
        ]
        
        self.proxies = {
            "http": f"{self.proxy_type}://{self.proxy_host}:{self.proxy_port}",
        }
    
    @property
    def random_headers(self):
        """Get random user agent headers."""
        return {
            'User-Agent': choice(self.desktop_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
    
    def discover_urls(self, search_terms: Optional[List[str]] = None) -> List[str]:
        """
        Discover .onion URLs from search engine.
        
        Args:
            search_terms: List of search terms (defaults to common terms)
            
        Returns:
            List of discovered .onion URLs
        """
        if not search_terms:
            search_terms = ['onion', 'darkweb', 'tor']
        
        self.logger.info(f'Connecting to {self.url}')
        headers = self.random_headers
        
        urls = []
        self.logger.info('Generating search URLs')
        
        for term in search_terms:
            # First page
            urls.append(
                f"{self.url}/4a1f6b371c/search.cgi?cmd=Search!&fmt=url&form=extended&GroupBySite=no&m=all&ps=50&q={term}&sp=1&sy=1&type=&ul=&wf=2221&wm=wrd"
            )
            # Additional pages
            for cont in range(1, 10):
                urls.append(
                    f"{self.url}/4a1f6b371c/search.cgi?cmd=Search!&fmt=url&form=extended&GroupBySite=no&m=all&np={cont}&ps=50&q={term}&sp=1&sy=1&type=&ul=&wf=2221&wm=wrd"
                )
        
        onionurls = []
        for url in urls:
            self.logger.debug(f'Connecting to {url}')
            try:
                request = self.session.get(
                    url,
                    proxies=self.proxies,
                    timeout=self.timeout,
                    headers=headers
                )
                
                if request.status_code == 200:
                    soup = BeautifulSoup(request.content, features="lxml")
                    for findurl in soup.find_all('dt'):
                        link = findurl.find('a')
                        if link and 'href' in link.attrs:
                            cleaned_url = link['href'] \
                                .replace('\xad', '') \
                                .replace('\n', '') \
                                .replace("http://", '') \
                                .replace("https://", '') \
                                .replace(r'\s', '') \
                                .replace('\t', '')
                            onionurls.append(cleaned_url)
            
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ReadTimeout,
                    requests.exceptions.InvalidURL) as e:
                self.logger.debug(f'Connection error: {e}')
                continue
        
        self.logger.info(f'Found {len(onionurls)} URLs from Search engine')
        return list(set(onionurls))  # Return unique URLs
