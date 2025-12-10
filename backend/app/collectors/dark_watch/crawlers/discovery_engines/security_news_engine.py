#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Security News Discovery Engine

Discovers .onion URLs from CyberSecurityNews Pastebin account.
"""

import requests
import re
import logging
from random import choice
import time
from bs4 import BeautifulSoup
from typing import List


class SecurityNewsEngine:
    """Engine for discovering URLs from CyberSecurityNews."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.session()
        self.desktop_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0'
        ]
    
    @property
    def random_headers(self):
        """Get random user agent headers."""
        return {
            'User-Agent': choice(self.desktop_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
    
    def discover_urls(self) -> List[str]:
        """
        Discover .onion URLs from CyberSecurityNews.
        
        Returns:
            List of discovered .onion URLs
        """
        self.logger.info("Starting CyberSecurityNews URL collection")
        onionurls = []
        
        try:
            headers = self.random_headers
            time.sleep(2)
            
            request = self.session.get(
                "https://pastebin.com/u/cybersecuritynews/1",
                headers=headers
            )
            
            if request.status_code != 200:
                self.logger.warning(f"Pastebin returned status {request.status_code}")
                return []
            
            soup = BeautifulSoup(request.content, features="lxml")
            
            # Get pagination
            pages_to_pages = []
            pagination_div = soup.find('div', {'class': 'pagination'})
            if pagination_div:
                for raw in pagination_div.findAll('a'):
                    pages_to_pages.append(raw.get_text())
            
            pages_urls = ["https://pastebin.com/u/cybersecuritynews/1"]
            if pages_to_pages:
                try:
                    max_page = int(pages_to_pages[-2])
                    for cont in range(2, max_page + 1):
                        pages_urls.append(
                            f"https://pastebin.com/u/cybersecuritynews/{cont}"
                        )
                except (ValueError, IndexError):
                    pass
            
            # Get raw paste URLs
            raw_urls = []
            for get_urls in pages_urls:
                self.logger.info(f'Connecting to {get_urls}')
                time.sleep(2)  # Rate limiting
                
                request = self.session.get(get_urls, headers=headers)
                if request.status_code == 200:
                    soup = BeautifulSoup(request.content, features="lxml")
                    table = soup.find('table', {'class': 'maintable'})
                    if table:
                        for raw in table.findAll('a'):
                            if 'href' in raw.attrs:
                                if 'archive' not in raw['href']:
                                    raw_urls.append(
                                        f"https://pastebin.com/raw{raw['href']}"
                                    )
            
            # Extract .onion URLs from raw pastes
            self.logger.info('Performing regex extraction. Please wait...')
            for raw_url in raw_urls:
                try:
                    time.sleep(1)  # Rate limiting
                    request = self.session.get(raw_url, headers=headers)
                    
                    if request.status_code == 200:
                        soup = BeautifulSoup(request.content, features="lxml")
                        body = soup.find('body')
                        
                        if body:
                            raw_text = body.get_text() \
                                .replace('\xad', ' ') \
                                .replace("http://", ' ') \
                                .replace("https://", ' ') \
                                .replace('.onion', '.onion ') \
                                .replace("\\/", "/")
                            
                            regex_match_onions = re.findall(
                                r"[A-Za-z0-9]{0,12}\.?[A-Za-z0-9]{12,62}\.onion",
                                raw_text,
                                re.DOTALL
                            )
                            onionurls.extend(regex_match_onions)
                
                except Exception as e:
                    self.logger.debug(f"Error processing paste {raw_url}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"SecurityNews engine error: {e}")
        
        self.logger.info(f'Found {len(onionurls)} URLs from SecurityNews')
        return list(set(onionurls))  # Return unique URLs
