#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Tor Connector for Dark Web Crawling

Adapted from VigilantOnion for keyword-focused URL discovery and monitoring.
"""

import os
import re
import json
import requests
import time
from random import choice
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional, Any
from loguru import logger
try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False

from app.config import settings
from .url_database import URLDatabase


class TorConnector:
    """Connector for crawling Tor network sites with keyword monitoring."""
    
    def __init__(
        self,
        urls: Optional[List] = None,
        proxy_host: Optional[str] = None,
        proxy_port: Optional[int] = None,
        proxy_type: Optional[str] = None,
        timeout: Optional[int] = None,
        count_categories: Optional[int] = None,
        score_categorie: Optional[int] = None,
        score_keywords: Optional[int] = None,
        db_path: Optional[str] = None,
        db_name: Optional[str] = None
    ):
        """
        Initialize Tor Connector.
        
        Args:
            urls: List of URLs to crawl
            proxy_host: Tor proxy host (defaults to settings)
            proxy_port: Tor proxy port (defaults to settings)
            proxy_type: Proxy type (defaults to settings)
            timeout: Request timeout (defaults to settings)
            count_categories: Max retry count for categories
            score_categorie: Minimum category score threshold
            score_keywords: Minimum keyword score threshold
            db_path: Database path (defaults to settings)
            db_name: Database name (defaults to settings)
        """
        # Use settings defaults if not provided
        self.proxy_host = proxy_host or settings.TOR_PROXY_HOST
        self.proxy_port = proxy_port or settings.TOR_PROXY_PORT
        self.proxy_type = proxy_type or settings.TOR_PROXY_TYPE
        self.timeout = timeout or settings.TOR_TIMEOUT
        self.count_categories = count_categories or settings.CRAWLER_COUNT_CATEGORIES
        self.score_categorie = score_categorie or settings.CRAWLER_SCORE_CATEGORIE
        self.score_keywords = score_keywords or settings.CRAWLER_SCORE_KEYWORDS
        
        logger.info(f"[TorConnector] Initializing with proxy={self.proxy_type}://{self.proxy_host}:{self.proxy_port}, timeout={self.timeout}")
        
        # Initialize database
        db_path = db_path or str(settings.DATA_DIR / settings.CRAWLER_DB_PATH)
        db_name = db_name or settings.CRAWLER_DB_NAME
        logger.info(f"[TorConnector] Connecting to database: {db_path}/{db_name}")
        self.database = URLDatabase(dbpath=db_path, dbname=db_name)
        logger.info(f"[TorConnector] Database connection established")
        
        self.urls = urls or []
        self.session = requests.session()
        self.desktop_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0'
        ]
        
        self.proxies = {
            "http": f"{self.proxy_type}://{self.proxy_host}:{self.proxy_port}",
        }
        logger.info(f"[TorConnector] Initialization complete")
    
    @property
    def headers(self):
        """Get random user agent headers."""
        return {
            'User-Agent': choice(self.desktop_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
    
    def check_yara(self, raw: str, yarafile: str) -> List:
        """
        Validate YARA rule to categorize sites.
        
        Args:
            raw: Text content to check
            yarafile: Path to YARA rule file
            
        Returns:
            List of YARA matches
        """
        if not YARA_AVAILABLE:
            logger.debug("[TorConnector] YARA not available, skipping rule check")
            return []
        
        if raw is None or not os.path.exists(yarafile):
            if not os.path.exists(yarafile):
                logger.warning(f"[TorConnector] YARA file not found: {yarafile}")
            return []
        
        try:
            rules = yara.compile(filepath=yarafile)
            matches = rules.match(data=raw.encode())
            return matches
        except Exception as e:
            logger.warning(f"[TorConnector] YARA rule check failed: {e}")
            return []
    
    def text(self, response: bytes) -> str:
        """
        Remove HTML tags and extract only text elements.
        
        Args:
            response: HTML response content
            
        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(response, features="lxml")
        for s in soup(['script', 'style']):
            s.decompose()
        
        return ' '.join(soup.stripped_strings)
    
    def crawler(self, url: List) -> Dict[str, Any]:
        """
        Crawl a single URL.
        
        Args:
            url: URL tuple from database (id, type, url, title, baseurl, status, ...)
            
        Returns:
            Dictionary with crawl results
        """
        if url is None or len(url) < 3:
            logger.warning("[TorConnector] Invalid URL tuple provided to crawler")
            return {}
        
        url_str = url[2]  # URL is at index 2
        url_id = url[0]   # ID is at index 0
        
        logger.info(f"[TorConnector] Starting crawl for URL: {url_str} (ID: {url_id})")
        crawl_start = time.time()
        
        try:
            logger.debug(
                f"[TorConnector] Making request to {url_str} via proxy {self.proxy_type}://{self.proxy_host}:{self.proxy_port}, "
                f"timeout={self.timeout}s"
            )
            request_start = time.time()
            request = self.session.get(
                f"http://{url_str}",
                proxies=self.proxies,
                headers=self.headers,
                timeout=self.timeout
            )
            request_time = time.time() - request_start
            response_size = len(request.content) if request.content else 0
            logger.info(
                f"[TorConnector] Request to {url_str} completed in {request_time:.2f}s - "
                f"Status: {request.status_code}, Response size: {response_size} bytes, "
                f"Content-Type: {request.headers.get('Content-Type', 'unknown')}"
            )
            
            if request.status_code == 200:
                logger.info(f"[TorConnector] Updating url status {url_str} for 200.")
                
                self.database.update_status(
                    id=url_id,
                    url=url_str,
                    result=200,
                    count_categories=self.count_categories
                )
                
                # Extract text content
                logger.debug(f"[TorConnector] Extracting text content from {url_str}")
                text_extract_start = time.time()
                text_content = self.text(response=request.content).lower()
                text_extract_time = time.time() - text_extract_start
                logger.info(f"[TorConnector] Extracted {len(text_content)} chars of text in {text_extract_time:.3f}s")
                
                # Check YARA rules for categories
                logger.debug(f"[TorConnector] Checking YARA rules for categories on {url_str}")
                yara_file_categories = os.path.join(
                    os.path.dirname(__file__), "..", "..", "..", "..", "data", "yara", "categories.yar"
                )
                yara_check_start = time.time()
                full_match_yara = self.check_yara(raw=text_content, yarafile=yara_file_categories)
                yara_check_time = time.time() - yara_check_start
                logger.info(f"[TorConnector] YARA category check completed in {yara_check_time:.3f}s, matches={len(full_match_yara)}")
                
                if len(full_match_yara) == 0:
                    full_match_yara_str = "no_match"
                    categorie = "no_match"
                    score_categorie = 0
                else:
                    full_match_yara_str = str(full_match_yara)
                    categorie = str(full_match_yara[0])
                    score_categorie = sum(int(match.meta.get('score', 0)) for match in full_match_yara)
                
                # Check YARA rules for keywords
                logger.debug(f"[TorConnector] Checking YARA rules for keywords on {url_str}")
                yara_file_keywords = os.path.join(
                    os.path.dirname(__file__), "..", "..", "..", "..", "data", "yara", "keywords.yar"
                )
                yara_keywords_start = time.time()
                full_match_keywords = self.check_yara(raw=text_content, yarafile=yara_file_keywords)
                yara_keywords_time = time.time() - yara_keywords_start
                logger.info(f"[TorConnector] YARA keyword check completed in {yara_keywords_time:.3f}s, matches={len(full_match_keywords)}, score={score_keywords if len(full_match_keywords) > 0 else 0}")
                
                if len(full_match_keywords) == 0:
                    full_match_keywords_str = "no_match"
                    score_keywords = 0
                else:
                    full_match_keywords_str = str(full_match_keywords)
                    score_keywords = sum(int(match.meta.get('score', 0)) for match in full_match_keywords)
                
                # Extract title
                logger.debug(f"[TorConnector] Extracting title from {url_str}")
                soup = BeautifulSoup(request.content, features="lxml")
                try:
                    title = soup.find('title').get_text() \
                        .replace(r'\s', '') \
                        .replace('\t', '') \
                        .replace('\n', '') \
                        .replace("'", "") \
                        .replace("  ", "") \
                        .replace("   ", "")
                    logger.info(f"[TorConnector] Extracted title: {title[:50]}..." if title and len(title) > 50 else f"[TorConnector] Extracted title: {title}")
                except:
                    title = None
                    logger.warning(f"[TorConnector] Could not extract title from {url_str}")
                
                # Update database
                logger.debug(f"[TorConnector] Updating database for {url_str}")
                self.database.update_categorie(
                    id=url_id,
                    categorie=categorie,
                    full_match_categorie=full_match_yara_str,
                    title=title,
                    score_categorie=score_categorie,
                    score_keywords=score_keywords,
                    full_match_keywords=full_match_keywords_str
                )
                
                total_crawl_time = time.time() - crawl_start
                logger.info(f"[TorConnector] Crawl completed for {url_str} in {total_crawl_time:.2f}s - Category: {categorie}, Score: {score_keywords}")
                
                return {
                    "status": "online",
                    "title": title,
                    "content": text_content,
                    "category": categorie,
                    "score_categorie": score_categorie,
                    "score_keywords": score_keywords,
                    "keywords_matched": full_match_keywords_str
                }
            else:
                logger.warning(f"[TorConnector] URL {url_str} returned status {request.status_code}")
                self.database.update_status(
                    id=url_id,
                    url=url_str,
                    result=404,
                    count_categories=self.count_categories
                )
                return {"status": "offline", "status_code": request.status_code}
                
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.InvalidURL) as e:
            error_time = time.time() - crawl_start
            error_type = type(e).__name__
            logger.error(
                f"[TorConnector] Connection error for {url_str} after {error_time:.2f}s - "
                f"Error type: {error_type}, Error: {str(e)}, "
                f"Proxy: {self.proxy_type}://{self.proxy_host}:{self.proxy_port}"
            )
            logger.info(f"[TorConnector] Could not connect to site. Updating url status {url_str} for 404.")
            self.database.update_status(
                id=url_id,
                url=url_str,
                result=404,
                count_categories=self.count_categories
            )
            return {"status": "error", "error": str(e)}
    
    def more_urls(self, url: str) -> Optional[List[str]]:
        """
        Extract more URLs from a page.
        
        Args:
            url: Base URL to extract links from
            
        Returns:
            List of discovered URLs
        """
        self.logger.info(f"Searching for new urls in: {url}")
        try:
            request = self.session.get(
                f"http://{url}",
                proxies=self.proxies,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if request.status_code == 200:
                pages = []
                soup = BeautifulSoup(request.content, features="lxml")
                try:
                    for raw in soup.find('body').findAll():
                        mosturl = str(raw.get('href'))
                        if raw.get('href') is not None:
                            if '/' in mosturl \
                                    and '/' != mosturl \
                                    and 'http://' not in mosturl \
                                    and 'https://' not in mosturl \
                                    and '://' not in mosturl \
                                    and 'www' not in mosturl \
                                    and ' ' not in mosturl \
                                    and "'" not in mosturl \
                                    and '(' not in mosturl \
                                    and '.m3u' not in mosturl \
                                    and '.zip' not in mosturl \
                                    and '.exe' not in mosturl \
                                    and '.onion' not in mosturl:
                                
                                pages.append(f"{url}{mosturl}")
                                self.logger.debug(f'Found URL: {url}{mosturl}')
                            
                            elif '/' not in mosturl \
                                    and '.m3u' not in mosturl \
                                    and '.zip' not in mosturl \
                                    and '.exe' not in mosturl \
                                    and url not in mosturl \
                                    and ('.php' in mosturl or '.htm' in mosturl) \
                                    and '.onion' not in mosturl:
                                pages.append(f"{url}/{mosturl}")
                                self.logger.debug(f'Found URL: {url}/{mosturl}')
                            
                            elif url in mosturl \
                                    and ('http://' in mosturl or 'https://' in mosturl) \
                                    and ('.php' in mosturl or '.htm' in mosturl):
                                pages.append(f"{mosturl}".replace('http://', '').replace('https://', ''))
                                self.logger.debug(f'Found URL: {mosturl}')
                            
                            elif '.onion' in mosturl \
                                    and '.m3u' not in mosturl \
                                    and '.zip' not in mosturl \
                                    and '.exe' not in mosturl \
                                    and 'http://' in mosturl \
                                    and url not in mosturl:
                                pages.append(f"{mosturl}".replace('http://', '').replace('https://', ''))
                                self.logger.debug(f'Found onion URL: {mosturl}')
                    
                    return pages
                    
                except AttributeError as e:
                    self.logger.error(f"No text found on page: {e}")
                    return []
                    
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.InvalidURL) as e:
            self.logger.debug(f"Error occurred: {str(e)}")
            return []
        
        return []
    
    def crawl_url(self, url_str: str) -> Dict[str, Any]:
        """
        Crawl a URL string directly (convenience method).
        
        Args:
            url_str: URL string to crawl
            
        Returns:
            Dictionary with crawl results
        """
        # Check if URL exists in database
        existing = self.database.select_url(url=url_str)
        
        if len(existing) == 0:
            # Save new URL
            self.database.save(
                url=url_str,
                source="Script",
                type="URI",
                baseurl=url_str
            )
            existing = self.database.select_url(url=url_str)
        
        if len(existing) > 0:
            return self.crawler(existing[0])
        
        return {}
