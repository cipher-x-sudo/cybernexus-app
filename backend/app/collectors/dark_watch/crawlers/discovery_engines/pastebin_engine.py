#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Pastebin Discovery Engine

Discovers .onion URLs from Pastebin pastes.
"""

import requests
import re
import logging
from random import choice
import time
from bs4 import BeautifulSoup
from typing import List, Optional


class PastebinEngine:
    """Engine for discovering URLs from Pastebin."""
    
    def __init__(self, paste_ids: Optional[str] = None):
        """
        Initialize Pastebin engine.
        
        Args:
            paste_ids: Comma-separated list of paste IDs (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.session = requests.session()
        self.paste_ids = paste_ids
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
    
    def discover_urls(self, paste_ids: Optional[str] = None) -> List[str]:
        """
        Discover .onion URLs from Pastebin.
        
        Args:
            paste_ids: Comma-separated list of paste IDs (uses instance var if not provided)
            
        Returns:
            List of discovered .onion URLs
        """
        ids = paste_ids or self.paste_ids
        if not ids:
            self.logger.warning("No paste IDs provided")
            return []
        
        self.logger.info("Starting Pastebin URL collection")
        urls_onion = []
        
        try:
            headers = self.random_headers
            
            for paste_id in ids.split(','):
                paste_id = paste_id.strip()
                if not paste_id:
                    continue
                
                try:
                    request = self.session.get(
                        f"https://pastebin.com/raw/{paste_id}",
                        headers=headers,
                        timeout=10
                    )
                    
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
                            urls_onion.extend(regex_match_onions)
                    
                    time.sleep(1)  # Rate limiting
                
                except Exception as e:
                    self.logger.debug(f"Error processing paste {paste_id}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Pastebin engine error: {e}")
        
        self.logger.info(f'Found {len(urls_onion)} URLs from Pastebin')
        return list(set(urls_onion))  # Return unique URLs
