#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Gist Discovery Engine

Discovers .onion URLs from GitHub Gist.
"""

import requests
import re
import logging
import urllib.parse
from random import choice
import time
from bs4 import BeautifulSoup
from typing import List


class GistEngine:
    """Engine for discovering URLs from GitHub Gist."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
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
        Discover .onion URLs from Gist.
        
        Returns:
            List of discovered .onion URLs
        """
        self.logger.info('Starting Gist scraping.')
        urls = []
        
        try:
            with requests.Session() as session:
                headers = self.random_headers
                
                # Get initial page
                request = session.get(
                    'https://gist.github.com/search?l=Text&q=.onion',
                    headers=headers
                )
                
                if request.status_code != 200:
                    self.logger.warning(f"Gist search returned status {request.status_code}")
                    return []
                
                # Get pagination
                soup = BeautifulSoup(request.content, features="lxml")
                pages = []
                search_urls = ["https://gist.github.com/search?l=Text&q=.onion"]
                
                try:
                    pagination_div = soup.find('div', {'class': 'pagination'})
                    if pagination_div:
                        for pagination in pagination_div.findAll('a'):
                            pages.append(pagination.get_text())
                except:
                    pages = []
                
                if pages:
                    try:
                        max_page = int(pages[-2])
                        for cont in range(2, max_page + 1):
                            full_url = f"https://gist.github.com/search?l=Text&p={cont}&q={urllib.parse.quote('.onion')}"
                            search_urls.append(full_url)
                    except (ValueError, IndexError):
                        pass
                
                # Scrape each page
                gist_urls = []
                for inurl in search_urls:
                    self.logger.debug(f"Connecting to {inurl}")
                    time.sleep(2)  # Rate limiting
                    request = session.get(inurl, headers=headers)
                    
                    if request.status_code == 200:
                        soup = BeautifulSoup(request.content, features="lxml")
                        for code in soup.findAll('div', {'class': 'gist-snippet'}):
                            if '.onion' in code.get_text().lower():
                                for raw in code.findAll('a', {'class': 'link-overlay'}):
                                    try:
                                        gist_urls.append(raw['href'])
                                    except:
                                        pass
                
                # Get raw content from gists
                for gist_url in gist_urls:
                    self.logger.debug(f"Fetching gist: {gist_url}")
                    time.sleep(2)  # Rate limiting
                    try:
                        request = session.get(gist_url, headers=headers)
                        
                        if request.status_code == 200:
                            soup = BeautifulSoup(request.content, features="lxml")
                            
                            for raw in soup.findAll('a', {'class': 'btn btn-sm'}):
                                try:
                                    raw_url = f"https://gist.githubusercontent.com{raw['href']}"
                                    
                                    # Fetch raw content
                                    if '.txt' in raw_url.lower() or '.csv' in raw_url.lower():
                                        time.sleep(2)
                                        raw_request = session.get(raw_url, headers=headers)
                                        if raw_request.status_code == 200:
                                            content = raw_request.text
                                            
                                            # Extract .onion URLs
                                            regex = re.compile(
                                                r"[A-Za-z0-9]{0,12}\.?[A-Za-z0-9]{12,50}\.onion"
                                            )
                                            
                                            for line in content.split('\n'):
                                                cleaned = line \
                                                    .replace('\xad', '') \
                                                    .replace('\n', '') \
                                                    .replace("http://", '') \
                                                    .replace("https://", '') \
                                                    .replace("www.", "")
                                                
                                                match = regex.match(cleaned)
                                                if match:
                                                    urls.append(match.group())
                                    
                                except Exception as e:
                                    self.logger.debug(f"Error processing gist: {e}")
                    
                    except (requests.exceptions.ConnectionError,
                            requests.exceptions.ChunkedEncodingError,
                            requests.exceptions.ReadTimeout,
                            requests.exceptions.InvalidURL) as e:
                        self.logger.debug(f"Connection error: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Gist engine error: {e}")
        
        self.logger.info(f'Found {len(urls)} URLs from Gist')
        return list(set(urls))  # Return unique URLs
