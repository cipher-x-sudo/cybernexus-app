#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Reddit Discovery Engine

Discovers .onion URLs from Reddit comments.
"""

import requests
import json
import re
import logging
from random import choice
from bs4 import BeautifulSoup
from typing import List, Optional


class RedditEngine:
    """Engine for discovering URLs from Reddit."""
    
    def __init__(self):
        self.session = requests.session()
        self.logger = logging.getLogger(__name__)
        self.source = 'Reddit'
        self.url = 'https://api.pushshift.io/reddit/search/comment/?subreddit=onions&limit=1000'
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
        Discover .onion URLs from Reddit.
        
        Returns:
            List of discovered .onion URLs
        """
        self.logger.info('Getting Reddit API information')
        onionurls = []
        
        try:
            request = self.session.get(self.url, headers=self.random_headers)
            
            if request.status_code != 200:
                self.logger.warning(f"Reddit API returned status {request.status_code}")
                return []
            
            loaded_json = json.loads(request.content)
            
            self.logger.info('Filtering URLs that have .onion in the text')
            for data in loaded_json.get('data', []):
                reddit_url = f"https://www.reddit.com{data.get('permalink', '')}"
                try:
                    request = self.session.get(reddit_url, headers=self.random_headers)
                    soup = BeautifulSoup(request.content, features="lxml")
                    
                    for raw in soup.findAll('a', {'rel': 'nofollow'}):
                        if 'href' in raw.attrs and 'https://' in raw['href']:
                            raw_text = self._extract_text(url=raw['href'])
                            if raw_text:
                                self.logger.debug('Applying regex')
                                regex = re.compile(
                                    r"[A-Za-z0-9]{0,12}\.?[A-Za-z0-9]{12,50}\.onion"
                                )
                                
                                for line in raw_text.split('\n'):
                                    cleaned = line \
                                        .replace('\xad', '') \
                                        .replace('\n', '') \
                                        .replace("http://", '') \
                                        .replace("https://", '') \
                                        .replace(r'\s', '') \
                                        .replace('\t', '')
                                    
                                    match = regex.match(cleaned)
                                    if match:
                                        onionurls.append(match.group())
                
                except (requests.exceptions.ConnectionError,
                        requests.exceptions.ChunkedEncodingError,
                        requests.exceptions.ReadTimeout,
                        requests.exceptions.InvalidURL) as e:
                    self.logger.debug(f"Connection error: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Reddit engine error: {e}")
        
        self.logger.info(f'Found {len(onionurls)} URLs from Reddit')
        return list(set(onionurls))  # Return unique URLs
    
    def _extract_text(self, url: str) -> Optional[str]:
        """
        Extract text content from URL.
        
        Args:
            url: URL to extract text from
            
        Returns:
            Extracted text or None
        """
        try:
            if url is not None:
                request = self.session.get(url, headers=self.random_headers)
                self.logger.debug(f'Connecting to {url} - {request.status_code}')
                
                if request.status_code == 200:
                    soup = BeautifulSoup(request.content, features="lxml")
                    for s in soup(['script', 'style']):
                        s.decompose()
                    
                    return ' '.join(soup.stripped_strings)
        
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.TooManyRedirects):
            pass
        
        return None
