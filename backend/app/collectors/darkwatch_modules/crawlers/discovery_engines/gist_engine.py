#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Gist Discovery Engine

Discovers .onion URLs from GitHub Gist.
"""

import requests
import re
import urllib.parse
from random import choice
import time
from bs4 import BeautifulSoup
from typing import List
from loguru import logger


class DummyLink:
    """Helper class to simulate a link object for constructed URLs"""
    def __init__(self, href):
        self.href = href
    
    def get(self, key, default=None):
        if key == 'href':
            return self.href
        return default


class GistEngine:
    """Engine for discovering URLs from GitHub Gist."""
    
    def __init__(self):
        self.logger = logger
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
                        
                        # Debug: Check what we're actually finding
                        gist_snippets = soup.findAll('div', {'class': 'gist-snippet'})
                        self.logger.info(f"Page {inurl}: Found {len(gist_snippets)} divs with class 'gist-snippet'")
                        
                        # Debug: Inspect first gist snippet in detail (first page only)
                        if inurl == search_urls[0] and len(gist_snippets) > 0:
                            first_snippet = gist_snippets[0]
                            snippet_text = first_snippet.get_text().lower()
                            has_onion = '.onion' in snippet_text
                            self.logger.info(f"Page {inurl}: First snippet contains '.onion': {has_onion}")
                            
                            # Check what links exist in the snippet
                            all_links_in_snippet = first_snippet.findAll('a', href=True)
                            self.logger.info(f"Page {inurl}: First snippet has {len(all_links_in_snippet)} links total")
                            
                            # Check for link-overlay specifically
                            link_overlays = first_snippet.findAll('a', {'class': 'link-overlay'})
                            self.logger.info(f"Page {inurl}: First snippet has {len(link_overlays)} links with class 'link-overlay'")
                            
                            # Log sample link hrefs
                            if all_links_in_snippet:
                                sample_hrefs = [link.get('href', '')[:100] for link in all_links_in_snippet[:3]]
                                self.logger.info(f"Page {inurl}: Sample link hrefs from first snippet: {sample_hrefs}")
                        
                        # Try multiple selector strategies
                        # Strategy 1: Find gist links in snippets containing .onion
                        snippets_with_onion = 0
                        for code in gist_snippets:
                            if '.onion' in code.get_text().lower():
                                snippets_with_onion += 1
                                # Find all links in this snippet
                                all_links = code.findAll('a', href=True)
                                for link in all_links:
                                    href = link.get('href', '')
                                    # Look for gist URL pattern: /username/gistid (not /forks, #comments, etc.)
                                    # Pattern: starts with /, has exactly one more /, and the part after second / is alphanumeric
                                    if href.startswith('/') and href.count('/') == 2 and not any(
                                        skip in href for skip in ['/forks', '/stargazers', '#comments', '/revisions']
                                    ):
                                        # Extract the gist ID part (after second /)
                                        parts = href.split('/')
                                        if len(parts) >= 3 and parts[2] and parts[2][0].isalnum():
                                            # This looks like a gist URL: /username/gistid
                                            # Convert to full URL
                                            full_url = f"https://gist.github.com{href}"
                                            if full_url not in gist_urls:
                                                gist_urls.append(full_url)
                                                break  # Found the main gist link, move to next snippet
                        
                        if len(gist_snippets) > 0:
                            self.logger.info(f"Page {inurl}: {snippets_with_onion} out of {len(gist_snippets)} snippets contain '.onion' text")
                        
                        # Strategy 2: Try finding all links that might be gist URLs (fallback if Strategy 1 fails)
                        if len(gist_urls) == gist_count_before:
                            self.logger.debug(f"Page {inurl}: Strategy 1 found no URLs, trying Strategy 2")
                            # Try alternative: look for links to gist.github.com
                            all_links = soup.findAll('a', href=True)
                            gist_links = [link for link in all_links if 'gist.github.com' in link.get('href', '') or 
                                         (link.get('href', '').startswith('/') and link.get('href', '').count('/') == 2)]
                            self.logger.debug(f"Page {inurl}: Found {len(gist_links)} potential gist links")
                            
                            # Try finding by data attributes or other patterns
                            for link in gist_links:
                                href = link.get('href', '')
                                # Use same pattern matching as Strategy 1
                                if href.startswith('/') and href.count('/') == 2 and not any(
                                    skip in href for skip in ['/forks', '/stargazers', '#comments', '/revisions']
                                ):
                                    parts = href.split('/')
                                    if len(parts) >= 3 and parts[2] and parts[2][0].isalnum():
                                        # Check if parent contains .onion
                                        parent = link.find_parent()
                                        if parent and '.onion' in parent.get_text().lower():
                                            full_url = f"https://gist.github.com{href}"
                                            if full_url not in gist_urls:
                                                gist_urls.append(full_url)
                                elif 'gist.github.com' in href:
                                    # Already a full URL, check if parent contains .onion
                                    parent = link.find_parent()
                                    if parent and '.onion' in parent.get_text().lower():
                                        if href not in gist_urls:
                                            gist_urls.append(href)
                        
                        # Strategy 3: Look for any div containing .onion and find nearby links (last resort fallback)
                        if len(gist_urls) == gist_count_before:
                            self.logger.debug(f"Page {inurl}: Strategy 2 found no URLs, trying Strategy 3")
                            onion_divs = soup.findAll(string=lambda text: text and '.onion' in text.lower())
                            self.logger.debug(f"Page {inurl}: Found {len(onion_divs)} text nodes containing '.onion'")
                            for text_node in onion_divs:
                                # Find parent and look for links nearby
                                parent = text_node.find_parent()
                                if parent:
                                    links = parent.findAll('a', href=True)
                                    for link in links:
                                        href = link.get('href', '')
                                        # Use same pattern matching as Strategy 1
                                        if href.startswith('/') and href.count('/') == 2 and not any(
                                            skip in href for skip in ['/forks', '/stargazers', '#comments', '/revisions']
                                        ):
                                            parts = href.split('/')
                                            if len(parts) >= 3 and parts[2] and parts[2][0].isalnum():
                                                full_url = f"https://gist.github.com{href}"
                                                if full_url not in gist_urls:
                                                    gist_urls.append(full_url)
                                                    break  # Found one, move to next text node
                                        elif 'gist.github.com' in href:
                                            if href not in gist_urls:
                                                gist_urls.append(href)
                                                break  # Found one, move to next text node
                        
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
                            
                            # Debug: Check if raw content links are found
                            raw_links = soup.findAll('a', {'class': 'btn btn-sm'})
                            self.logger.info(f"Gist {gist_url}: Found {len(raw_links)} links with class 'btn btn-sm'")
                            
                            # If no links found, try alternative selectors
                            if len(raw_links) == 0:
                                # Try finding raw links by href pattern
                                all_links = soup.findAll('a', href=True)
                                raw_links = [link for link in all_links if 'raw' in link.get('href', '').lower() or 'gist.githubusercontent.com' in link.get('href', '')]
                                self.logger.info(f"Gist {gist_url}: Found {len(raw_links)} links containing 'raw' or 'gist.githubusercontent.com'")
                                
                                # If still no links, try to find file links in the gist
                                if len(raw_links) == 0:
                                    # Look for file links - they might have different classes
                                    file_links = soup.findAll('a', href=lambda x: x and ('/raw/' in x or x.endswith('.txt') or x.endswith('.csv')))
                                    self.logger.info(f"Gist {gist_url}: Found {len(file_links)} file links")
                                    raw_links = file_links
                            
                            # If still no raw links found, try to find file information from the gist page
                            if len(raw_links) == 0:
                                # Look for file names in the gist HTML - they're often in data attributes or specific divs
                                # Try finding file links by looking for elements with file-related classes or data attributes
                                file_elements = soup.findAll(['a', 'span', 'div'], 
                                                             class_=lambda x: x and any(term in ' '.join(x).lower() 
                                                                                        for term in ['file', 'filename', 'gist-file']))
                                self.logger.info(f"Gist {gist_url}: Found {len(file_elements)} file-related elements")
                                
                                # Extract username and gistid for fallback construction
                                try:
                                    gist_parts = gist_url.replace('https://gist.github.com/', '').split('/')
                                    if len(gist_parts) >= 2:
                                        username = gist_parts[0]
                                        gistid = gist_parts[1]
                                        
                                        # Try to find actual filenames in the page
                                        # Look for data attributes or text that might indicate filenames
                                        potential_files = []
                                        for elem in file_elements:
                                            # Check data attributes
                                            for attr in elem.attrs:
                                                if 'file' in attr.lower() and elem.attrs[attr]:
                                                    potential_files.append(elem.attrs[attr])
                                            # Check text content that looks like filenames
                                            text = elem.get_text().strip()
                                            if text and ('.txt' in text.lower() or '.csv' in text.lower() or len(text.split('.')) == 2):
                                                potential_files.append(text)
                                        
                                        # If we found potential files, use them; otherwise try GitHub API
                                        if potential_files:
                                            for filename in set(potential_files[:3]):  # Limit to first 3 unique files
                                                raw_links.append(DummyLink(f"/{username}/{gistid}/raw/{filename}"))
                                            self.logger.info(f"Gist {gist_url}: Constructed {len(raw_links)} raw URLs from found filenames")
                                        else:
                                            # Last resort: try GitHub gist API endpoint (no auth needed for public gists)
                                            try:
                                                api_url = f"https://api.github.com/gists/{gistid}"
                                                api_response = session.get(api_url, headers=headers, timeout=5)
                                                if api_response.status_code == 200:
                                                    gist_data = api_response.json()
                                                    files = gist_data.get('files', {})
                                                    for filename in list(files.keys())[:3]:  # Limit to first 3 files
                                                        raw_links.append(DummyLink(f"/{username}/{gistid}/raw/{filename}"))
                                                    self.logger.info(f"Gist {gist_url}: Found {len(raw_links)} files via GitHub API")
                                            except Exception as api_e:
                                                self.logger.debug(f"Gist {gist_url}: GitHub API fallback failed: {api_e}")
                                except Exception as e:
                                    self.logger.warning(f"Gist {gist_url}: Could not construct fallback URLs: {e}")
                            
                            for raw in raw_links:
                                try:
                                    href = raw.get('href', '')
                                    self.logger.debug(f"Gist {gist_url}: Processing raw link with href: {href}")
                                    
                                    # Handle both relative and absolute URLs
                                    if href.startswith('/'):
                                        raw_url = f"https://gist.githubusercontent.com{href}"
                                    elif 'gist.githubusercontent.com' in href:
                                        raw_url = href
                                    else:
                                        # Try constructing from gist URL
                                        # Extract username and gistid from gist_url
                                        # Format: https://gist.github.com/username/gistid
                                        gist_parts = gist_url.replace('https://gist.github.com/', '').split('/')
                                        if len(gist_parts) >= 2:
                                            username = gist_parts[0]
                                            gistid = gist_parts[1]
                                            # Try default raw URL pattern
                                            raw_url = f"https://gist.githubusercontent.com/{username}/{gistid}/raw/"
                                            self.logger.info(f"Gist {gist_url}: Constructed raw URL: {raw_url}")
                                        else:
                                            continue
                                    
                                    # Fetch raw content - try all files that have a filename (not just .txt/.csv)
                                    # Skip if URL ends with just '/raw/' (no filename)
                                    # But allow any file that has /raw/ in the path with a filename after it
                                    has_filename = '/raw/' in raw_url and not raw_url.endswith('/raw/')
                                    should_fetch = has_filename
                                    
                                    if not should_fetch:
                                        self.logger.debug(f"Gist {gist_url}: Skipping raw URL (no filename): {raw_url}")
                                    
                                    if should_fetch:
                                        self.logger.info(f"Fetching raw content: {raw_url}")
                                        time.sleep(0.5)  # Reduced rate limiting
                                        try:
                                            raw_request = session.get(raw_url, headers=headers, timeout=10)
                                            self.logger.info(f"Raw content fetch: {raw_url} - status_code={raw_request.status_code}, size={len(raw_request.content) if raw_request.status_code == 200 else 0} bytes")
                                            
                                            if raw_request.status_code == 200:
                                                content = raw_request.text
                                                self.logger.debug(f"Raw content preview (first 200 chars): {content[:200]}")
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
            self.logger.exception(f"Gist engine error: {e}")
        
        unique_urls = list(set(urls))
        self.logger.info(f'Gist engine summary: found {len(urls)} total URLs, {len(unique_urls)} unique URLs')
        return unique_urls  # Return unique URLs
