#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
OnionSearch Library

Refactored from OnionSearch project to work as a library.
Supports ahmia, tor66, and onionland search engines.
"""

import logging
import math
import re
import time
from random import choice
from typing import List, Dict, Optional
from urllib.parse import quote, unquote, parse_qs, urlparse, urlencode

import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import ProtocolError, MaxRetryError, NewConnectionError
from loguru import logger as loguru_logger
from app.config import settings

logger = logging.getLogger(__name__)

# Engine URLs
ENGINES = {
    "ahmia": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion",
    "tor66": "http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion",
    "onionland": "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion",
}

desktop_agents = [
    'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0',  # Tor Browser for Windows and Linux
    'Mozilla/5.0 (Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0',  # Tor Browser for Android
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
]


def random_headers():
    """Generate random headers for requests"""
    return {'User-Agent': choice(desktop_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}


def clear(text: str) -> str:
    """Clean and normalize text"""
    cleaned = text.replace("\n", " ")
    cleaned = ' '.join(cleaned.split())
    return cleaned


def get_parameter(url: str, parameter_name: str, default=None):
    """Extract a parameter from URL query string, return default if not found"""
    try:
        parsed = urlparse.urlparse(url)
        params = parse_qs(parsed.query)
        if parameter_name in params and len(params[parameter_name]) > 0:
            return params[parameter_name][0]
        return default
    except (KeyError, IndexError, AttributeError) as e:
        logger.debug(f"Failed to get parameter '{parameter_name}' from URL '{url}': {e}")
        return default


def safe_request(
    method: str,
    url: str,
    proxies: Dict[str, str],
    timeout: int = 30,
    max_retries: int = 2,
    headers: Optional[Dict[str, str]] = None,
    debug: bool = False
):
    """
    Make a request with timeout, retry logic, and better error handling
    
    Args:
        method: HTTP method (GET or POST)
        url: URL to request
        proxies: Proxy configuration dict
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        headers: Request headers (defaults to random headers)
        debug: Enable debug logging
        
    Returns:
        Response object
        
    Raises:
        requests.exceptions.RequestException on failure
    """
    if headers is None:
        headers = random_headers()
    
    retries = 0
    last_exception = None
    
    while retries <= max_retries:
        try:
            if method.upper() == 'GET':
                response = requests.get(url, proxies=proxies, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, proxies=proxies, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if debug:
                logger.debug(f"Request to {url} returned status {response.status_code}")
            
            return response
        
        except (ConnectionError, NewConnectionError, MaxRetryError) as e:
            last_exception = e
            error_msg = str(e)
            retries += 1
            
            if "Connection refused" in error_msg or "Failed to establish a new connection" in error_msg:
                if retries <= max_retries:
                    wait_time = min(2 ** retries, 10)  # Exponential backoff, max 10 seconds
                    time.sleep(wait_time)
                else:
                    logger.error(f"✗ Failed to connect to {url} after {max_retries + 1} attempts: {e}")
                    raise
            else:
                logger.error(f"✗ Connection error to {url}: {e}")
                raise
        
        except requests.exceptions.Timeout as e:
            last_exception = e
            retries += 1
            if retries <= max_retries:
                wait_time = min(2 ** retries, 10)
                time.sleep(wait_time)
            else:
                logger.error(f"✗ Request timeout for {url} after {max_retries + 1} attempts")
                raise
        
        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.error(f"✗ Request error for {url}: {e}")
            raise
        
        except Exception as e:
            last_exception = e
            logger.error(f"✗ Unexpected error for {url}: {type(e).__name__}: {e}")
            raise
    
    # If we get here, all retries failed
    if last_exception:
        raise last_exception


def link_finder(engine_str: str, data_obj, debug: bool = False) -> List[Dict[str, str]]:
    """
    Extract links from search engine results
    
    Args:
        engine_str: Engine name (ahmia, tor66, onionland)
        data_obj: BeautifulSoup object or dict with results
        debug: Enable debug logging
        
    Returns:
        List of dicts with 'link' and 'name' keys
    """
    found_links = []
    name = ""
    link = ""

    def add_link():
        found_links.append({"engine": engine_str, "name": name, "link": link})

    if engine_str == "ahmia":
        # Try multiple selectors as Ahmia structure may have changed
        selectors = [
            'li.result h4 a',
            '.result h4 a',
            'div.result h4 a',
            'li.result a',
        ]
        found = False
        for selector in selectors:
            results_elems = data_obj.select(selector)
            if results_elems:
                if debug:
                    logger.debug(f"Ahmia: Using selector '{selector}' found {len(results_elems)} elements")
                for r in results_elems:
                    try:
                        href = r.get('href', '')
                        if 'redirect_url=' in href:
                            name = clear(r.get_text())
                            link = href.split('redirect_url=')[1].split('&')[0]  # Handle additional params
                            add_link()
                            found = True
                    except (KeyError, IndexError, AttributeError) as e:
                        if debug:
                            logger.debug(f"Ahmia: Error parsing result: {e}")
                        continue
                if found:
                    break
        if not found and debug:
            logger.debug("Ahmia: No results found with any selector")

    elif engine_str == "onionland":
        for r in data_obj.select('.result-block .title a'):
            try:
                if not r['href'].startswith('/ads/'):
                    name = clear(r.get_text())
                    link_param = get_parameter(r['href'], 'l')
                    if link_param:
                        link = unquote(unquote(link_param))
                        add_link()
                    else:
                        logger.debug(f"OnionLand: Missing 'l' parameter in URL: {r['href']}")
            except (KeyError, AttributeError, TypeError) as e:
                logger.debug(f"OnionLand: Error parsing result link: {e}")
                continue

    elif engine_str == "tor66":
        hr_tag = data_obj.find('hr')
        if hr_tag:
            for i in hr_tag.find_all_next('b'):
                try:
                    anchor = i.find('a')
                    # Fix: Check for href using get() instead of 'in' operator
                    if anchor and anchor.get('href'):
                        name = clear(anchor.get_text())
                        link = clear(anchor.get('href'))
                        # Filter out service info and other non-result links
                        if link and '.onion' in link and '/serviceinfo/' not in link:
                            add_link()
                except (KeyError, AttributeError, TypeError) as e:
                    if debug:
                        logger.debug(f"Tor66: Error parsing result: {e}")
                    continue
        else:
            if debug:
                logger.debug("Tor66: No <hr> tag found in results")

    return found_links


def ahmia(
    searchstr: str,
    proxies: Dict[str, str],
    timeout: int = 30,
    max_retries: int = 2,
    debug: bool = False
) -> List[Dict[str, str]]:
    """
    Search using Ahmia engine
    
    Args:
        searchstr: Search query string
        proxies: Proxy configuration dict
        timeout: Request timeout
        max_retries: Maximum retries
        debug: Enable debug logging
        
    Returns:
        List of result dicts with 'link', 'name', 'engine' keys
    """
    results = []
    # Ahmia requires a CSRF token from the search form
    ahmia_base = ENGINES['ahmia']
    
    try:
        # First, get the search page to extract the CSRF token
        if debug:
            logger.debug(f"Ahmia: Getting search page to extract CSRF token")
        search_page_resp = safe_request(
            'GET', ahmia_base + "/",
            proxies=proxies,
            headers=random_headers(),
            timeout=timeout,
            max_retries=max_retries,
            debug=debug
        )
        search_page_soup = BeautifulSoup(search_page_resp.text, 'html5lib')
        
        # Extract hidden form fields (CSRF token)
        csrf_params = {}
        forms = search_page_soup.find_all('form')
        for form in forms:
            hidden_inputs = form.find_all('input', type='hidden')
            for inp in hidden_inputs:
                csrf_params[inp.get('name')] = inp.get('value', '')
        
        # Build search URL with CSRF token
        search_params = {'q': searchstr}
        search_params.update(csrf_params)
        
        # Construct URL with parameters
        ahmia_search_url = ahmia_base + "/search/?" + urlencode(search_params)
        
        if debug:
            logger.debug(f"Ahmia: Requesting search with CSRF token: {ahmia_search_url[:150]}...")
        
        response = safe_request(
            'GET', ahmia_search_url,
            proxies=proxies,
            headers=random_headers(),
            timeout=timeout,
            max_retries=max_retries,
            debug=debug
        )
        soup = BeautifulSoup(response.text, 'html5lib')
        results = link_finder("ahmia", soup, debug=debug)
        if debug:
            logger.debug(f"Ahmia: Found {len(results)} results")
    except Exception as e:
        logger.error(f"Ahmia: Failed to fetch results: {e}")
        if debug:
            import traceback
            logger.debug(traceback.format_exc())

    return results


def tor66(
    searchstr: str,
    proxies: Dict[str, str],
    timeout: int = 30,
    max_retries: int = 2,
    max_pages: int = 30,
    debug: bool = False
) -> List[Dict[str, str]]:
    """
    Search using Tor66 engine
    
    Args:
        searchstr: Search query string
        proxies: Proxy configuration dict
        timeout: Request timeout
        max_retries: Maximum retries
        max_pages: Maximum pages to fetch
        debug: Enable debug logging
        
    Returns:
        List of result dicts with 'link', 'name', 'engine' keys
    """
    results = []
    tor66_url = ENGINES['tor66'] + "/search?q={}&sorttype=rel&page={}"
    
    try:
        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()

            url = tor66_url.format(quote(searchstr), 1)
            if debug:
                logger.debug(f"Tor66: Requesting {url}")
            
            resp = safe_request(
                'GET', url,
                proxies=proxies,
                headers=random_headers(),
                timeout=timeout,
                max_retries=max_retries,
                debug=debug
            )
            soup = BeautifulSoup(resp.text, 'html5lib')

            page_number = 1
            approx_re = re.search(r"\.Onion\ssites\sfound\s:\s([0-9]+)", resp.text)
            if approx_re is not None:
                nb_res = int(approx_re.group(1))
                results_per_page = 20
                page_number = math.ceil(float(nb_res / results_per_page))
                if page_number > max_pages:
                    page_number = max_pages

            results = link_finder("tor66", soup, debug=debug)

            for n in range(2, page_number + 1):
                try:
                    url = tor66_url.format(quote(searchstr), n)
                    resp = safe_request(
                        'GET', url,
                        proxies=proxies,
                        headers=random_headers(),
                        timeout=timeout,
                        max_retries=max_retries,
                        debug=debug
                    )
                    soup = BeautifulSoup(resp.text, 'html5lib')
                    ret = link_finder("tor66", soup, debug=debug)
                    results.extend(ret)
                except (requests.exceptions.RequestException, ConnectionError) as e:
                    logger.warning(f"Tor66: Error fetching page {n}: {e}")
                    if debug:
                        import traceback
                        logger.debug(traceback.format_exc())
                    break  # Stop if we hit an error on subsequent pages

    except Exception as e:
        logger.error(f"Tor66: Failed to fetch results: {e}")
        if debug:
            import traceback
            logger.debug(traceback.format_exc())

    return results


def onionland(
    searchstr: str,
    proxies: Dict[str, str],
    timeout: int = 30,
    max_retries: int = 2,
    max_pages: int = 100,
    debug: bool = False
) -> List[Dict[str, str]]:
    """
    Search using OnionLand engine
    
    Args:
        searchstr: Search query string
        proxies: Proxy configuration dict
        timeout: Request timeout
        max_retries: Maximum retries
        max_pages: Maximum pages to fetch
        debug: Enable debug logging
        
    Returns:
        List of result dicts with 'link', 'name', 'engine' keys
    """
    results = []
    onionlandv3_url = ENGINES['onionland'] + "/search?q={}&page={}"

    try:
        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()

            url = onionlandv3_url.format(quote(searchstr), 1)
            if debug:
                logger.debug(f"OnionLand: Requesting {url}")
            
            resp = safe_request(
                'GET', url,
                proxies=proxies,
                headers=random_headers(),
                timeout=timeout,
                max_retries=max_retries,
                debug=debug
            )
            soup = BeautifulSoup(resp.text, 'html5lib')

            page_number = 1
            try:
                for i in soup.find_all('div', attrs={"class": "search-status"}):
                    status_div = i.find('div', attrs={'class': "col-sm-12"})
                    if status_div:
                        approx_re = re.match(r"About ([,0-9]+) result(.*)", clear(status_div.get_text()))
                        if approx_re is not None:
                            nb_res = int((approx_re.group(1)).replace(",", ""))
                            results_per_page = 19
                            page_number = math.ceil(nb_res / results_per_page)
                            if page_number > max_pages:
                                page_number = max_pages
                            break
            except Exception as e:
                logger.debug(f"OnionLand: Could not determine page count: {e}")
                page_number = 1

            results = link_finder("onionland", soup, debug=debug)

            for n in range(2, page_number + 1):
                try:
                    url = onionlandv3_url.format(quote(searchstr), n)
                    resp = safe_request(
                        'GET', url,
                        proxies=proxies,
                        headers=random_headers(),
                        timeout=timeout,
                        max_retries=max_retries,
                        debug=debug
                    )
                    soup = BeautifulSoup(resp.text, 'html5lib')
                    ret = link_finder("onionland", soup, debug=debug)
                    if len(ret) == 0:
                        break
                    results.extend(ret)
                except Exception as e:
                    logger.error(f"OnionLand: Error fetching page {n}: {e}")
                    break

    except Exception as e:
        logger.error(f"OnionLand: Failed to fetch results: {e}")
        if debug:
            import traceback
            logger.debug(traceback.format_exc())

    return results


def search_all_engines(
    searchstr: str,
    proxies: Dict[str, str],
    engines: List[str] = None,
    timeout: int = 30,
    max_retries: int = 2,
    max_pages: int = 5,
    debug: bool = False
) -> List[str]:
    """
    Search all specified engines and return unique URLs
    
    Args:
        searchstr: Search query string
        proxies: Proxy configuration dict
        engines: List of engine names to use (default: ['ahmia', 'tor66', 'onionland'])
        timeout: Request timeout
        max_retries: Maximum retries
        max_pages: Maximum pages per engine
        debug: Enable debug logging
        
    Returns:
        List of unique .onion URLs
    """
    if engines is None:
        engines = ['ahmia', 'tor66', 'onionland']
    
    all_results = []
    engine_functions = {
        'ahmia': ahmia,
        'tor66': tor66,
        'onionland': onionland,
    }
    
    for engine_name in engines:
        if engine_name not in engine_functions:
            logger.warning(f"Unknown engine: {engine_name}, skipping")
            continue
        
        try:
            logger.debug(f"Searching {engine_name} for: {searchstr}")
            engine_func = engine_functions[engine_name]
            
            # Call engine function with appropriate parameters
            if engine_name == 'ahmia':
                results = engine_func(searchstr, proxies, timeout, max_retries, debug)
            else:
                results = engine_func(searchstr, proxies, timeout, max_retries, max_pages, debug)
            
            all_results.extend(results)
            logger.info(f"{engine_name}: Found {len(results)} results")
        except Exception as e:
            logger.error(f"{engine_name}: Error during search: {e}", exc_info=debug)
            continue
    
    # Extract unique URLs from results
    unique_urls = set()
    for result in all_results:
        link = result.get('link', '').strip()
        if link and link.endswith('.onion'):
            # Ensure it starts with http://
            if not link.startswith('http'):
                link = f"http://{link}"
            unique_urls.add(link)
    
    logger.info(f"Total unique URLs found: {len(unique_urls)}")
    return list(unique_urls)


class DarkWebEngine:
    """Engine for discovering URLs from OnionSearch engines."""
    
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
        self.proxy_host = proxy_host or settings.TOR_PROXY_HOST
        self.proxy_port = proxy_port or settings.TOR_PROXY_PORT
        self.proxy_type = proxy_type or settings.TOR_PROXY_TYPE
        
        self.proxies = {
            "http": f"{self.proxy_type}://{self.proxy_host}:{self.proxy_port}",
        }
        
        # Get configured engines (default: ahmia, tor66, onionland)
        self.engines = settings.ONIONSEARCH_ENGINES
        self.timeout = settings.ONIONSEARCH_TIMEOUT
        self.max_pages = settings.ONIONSEARCH_MAX_PAGES
        
        loguru_logger.info(
            f"[DarkWebEngine] Initialized with proxy={self.proxy_type}://{self.proxy_host}:{self.proxy_port}, "
            f"engines={self.engines}, timeout={self.timeout}s, max_pages={self.max_pages}"
        )
    
    def discover_urls(self, keywords: Optional[List[str]] = None) -> List[str]:
        """
        Discover .onion URLs using OnionSearch engines.
        
        Args:
            keywords: List of search keywords (defaults to generic terms if not provided)
        
        Returns:
            List of discovered .onion URLs
        """
        discovery_start = time.time()
        
        # Use keywords if provided, otherwise use generic search terms
        if keywords and len(keywords) > 0:
            search_queries = [kw.strip() for kw in keywords if kw.strip()]
        else:
            search_queries = ['onion', 'darkweb', 'tor']
        
        if not search_queries:
            loguru_logger.warning("[DarkWebEngine] No valid search queries provided")
            return []
        
        loguru_logger.info(f"[DarkWebEngine] Starting discovery with {len(search_queries)} search queries: {search_queries}")
        
        all_urls = []
        
        try:
            # Search each query across all engines
            for query in search_queries:
                loguru_logger.debug(f"[DarkWebEngine] Searching for: {query}")
                query_start = time.time()
                
                try:
                    urls = search_all_engines(
                        searchstr=query,
                        proxies=self.proxies,
                        engines=self.engines,
                        timeout=self.timeout,
                        max_retries=2,
                        max_pages=self.max_pages,
                        debug=settings.DEBUG
                    )
                    
                    query_time = time.time() - query_start
                    loguru_logger.info(
                        f"[DarkWebEngine] Query '{query}' found {len(urls)} URLs in {query_time:.2f}s"
                    )
                    all_urls.extend(urls)
                    
                except Exception as e:
                    query_time = time.time() - query_start
                    loguru_logger.error(
                        f"[DarkWebEngine] Error searching for '{query}' after {query_time:.2f}s: {e}",
                        exc_info=settings.DEBUG
                    )
                    continue
            
            # Remove duplicates and filter to .onion URLs only
            unique_urls = []
            seen = set()
            for url in all_urls:
                # Normalize URL
                normalized = url.strip().lower()
                if normalized not in seen and '.onion' in normalized:
                    seen.add(normalized)
                    unique_urls.append(url)
            
            total_time = time.time() - discovery_start
            loguru_logger.info(
                f"[DarkWebEngine] Discovery completed in {total_time:.2f}s. "
                f"Found {len(unique_urls)} unique .onion URLs from {len(all_urls)} total results"
            )
            return unique_urls
        
        except Exception as e:
            error_time = time.time() - discovery_start
            loguru_logger.error(f"[DarkWebEngine] Error after {error_time:.2f}s: {e}", exc_info=True)
            return []

