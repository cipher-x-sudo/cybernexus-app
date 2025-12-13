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
                    headers=headers,
                    timeout=10
                )
                
                # Log initial request status
                self.logger.info(f"Initial Gist search request: status_code={request.status_code}, response_size={len(request.content)} bytes")
                
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
                        # Limit to max 5 pages to prevent excessive scraping
                        max_pages_limit = 5
                        max_page = min(max_page, max_pages_limit)
                        for cont in range(2, max_page + 1):
                            full_url = f"https://gist.github.com/search?l=Text&p={cont}&q={urllib.parse.quote('.onion')}"
                            search_urls.append(full_url)
                    except (ValueError, IndexError):
                        pass
                
                # Scrape each page (limit to first 5 pages)
                search_urls = search_urls[:5]
                
                # Log pagination parsing results
                max_page_value = 'N/A'
                if pages and len(pages) >= 2:
                    try:
                        max_page_value = int(pages[-2])
                    except (ValueError, IndexError):
                        pass
                self.logger.info(f"Pagination parsing: found {len(pages)} page indicators, max_page={max_page_value}, will process {len(search_urls)} search URLs")
                
                gist_urls = []
                for inurl in search_urls:
                    self.logger.info(f"Scraping page: {inurl}")
                    self.logger.debug(f"Connecting to {inurl}")
                    time.sleep(0.5)  # Reduced rate limiting
                    try:
                        request = session.get(inurl, headers=headers, timeout=10)
                    except requests.exceptions.Timeout:
                        self.logger.warning(f"Timeout connecting to {inurl}")
                        continue
                    except requests.exceptions.RequestException as e:
                        self.logger.debug(f"Request error for {inurl}: {e}")
                        continue
                    
                    if request.status_code == 200:
                        soup = BeautifulSoup(request.content, features="lxml")
                        gist_count_before = len(gist_urls)
                        for code in soup.findAll('div', {'class': 'gist-snippet'}):
                            if '.onion' in code.get_text().lower():
                                for raw in code.findAll('a', {'class': 'link-overlay'}):
                                    try:
                                        gist_urls.append(raw['href'])
                                    except:
                                        pass
                        gist_count_after = len(gist_urls)
                        gists_found_this_page = gist_count_after - gist_count_before
                        self.logger.info(f"Page {inurl}: found {gists_found_this_page} gist URLs (total so far: {gist_count_after})")
                
                self.logger.info(f"Page scraping complete: found {len(gist_urls)} total gist URLs across all pages")
                
                # Get raw content from gists (limit to max 20 gists)
                max_gists_limit = 20
                total_gists_found = len(gist_urls)
                gist_urls = gist_urls[:max_gists_limit]
                self.logger.info(f"Gist processing: will process {len(gist_urls)} gists (limited from {total_gists_found} total)")
                for gist_url in gist_urls:
                    self.logger.info(f"Fetching gist: {gist_url}")
                    time.sleep(0.5)  # Reduced rate limiting
                    try:
                        request = session.get(gist_url, headers=headers, timeout=10)
                        self.logger.info(f"Gist fetch result: {gist_url} - status_code={request.status_code}")
                        
                        if request.status_code == 200:
                            soup = BeautifulSoup(request.content, features="lxml")
                            
                            for raw in soup.findAll('a', {'class': 'btn btn-sm'}):
                                try:
                                    raw_url = f"https://gist.githubusercontent.com{raw['href']}"
                                    
                                    # Fetch raw content
                                    if '.txt' in raw_url.lower() or '.csv' in raw_url.lower():
                                        self.logger.info(f"Fetching raw content: {raw_url}")
                                        time.sleep(0.5)  # Reduced rate limiting
                                        try:
                                            raw_request = session.get(raw_url, headers=headers, timeout=10)
                                            if raw_request.status_code == 200:
                                                content = raw_request.text
                                                urls_before = len(urls)
                                                
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
                                                
                                                urls_after = len(urls)
                                                urls_found_this_gist = urls_after - urls_before
                                                self.logger.info(f"Raw content extraction: {raw_url} - extracted {urls_found_this_gist} URLs (total so far: {urls_after})")
                                            else:
                                                self.logger.warning(f"Raw content fetch failed: {raw_url} - status_code={raw_request.status_code}")
                                        except requests.exceptions.Timeout:
                                            self.logger.warning(f"Timeout fetching raw content: {raw_url}")
                                            continue
                                        except requests.exceptions.RequestException as e:
                                            self.logger.warning(f"Request error for raw content {raw_url}: {e}")
                                            continue
                                    
                                except Exception as e:
                                    self.logger.debug(f"Error processing gist: {e}")
                    except requests.exceptions.Timeout:
                        self.logger.warning(f"Timeout fetching gist: {gist_url}")
                        continue
                    except requests.exceptions.RequestException as e:
                        self.logger.warning(f"Request error for gist {gist_url}: {e}")
                        continue
                    
                    except (requests.exceptions.ConnectionError,
                            requests.exceptions.ChunkedEncodingError,
                            requests.exceptions.ReadTimeout,
                            requests.exceptions.Timeout,
                            requests.exceptions.InvalidURL,
                            requests.exceptions.RequestException) as e:
                        self.logger.warning(f"Connection error for gist {gist_url}: {e}")
                        continue
        
        except Exception as e:
            self.logger.error(f"Gist engine error: {e}", exc_info=True)
        
        unique_urls = list(set(urls))
        self.logger.info(f'Gist engine summary: found {len(urls)} total URLs, {len(unique_urls)} unique URLs')
        return unique_urls  # Return unique URLs
