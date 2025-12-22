#!/usr/bin/python3
# -*- coding: utf-8 -*-



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
    
    return {'User-Agent': choice(desktop_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}


def clear(text: str) -> str:
    
    cleaned = text.replace("\n", " ")
    cleaned = ' '.join(cleaned.split())
    return cleaned


def get_parameter(url: str, parameter_name: str, default=None):
    
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
    timeout: Optional[int] = None,
    max_retries: int = 2,
    headers: Optional[Dict[str, str]] = None,
    debug: bool = False
):
    
    if headers is None:
        headers = random_headers()
    
    retries = 0
    last_exception = None
    request_start = time.time()
    
    loguru_logger.debug(f"[OnionSearch] [safe_request] {method} {url[:100]}... (timeout={timeout}s, retries={max_retries})")
    
    while retries <= max_retries:
        try:
            if method.upper() == 'GET':
                response = requests.get(url, proxies=proxies, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, proxies=proxies, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            request_time = time.time() - request_start
            loguru_logger.debug(
                f"[OnionSearch] [safe_request] {method} {url[:100]}... "
                f"returned {response.status_code} in {request_time:.2f}s"
            )
            
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
                    loguru_logger.warning(
                        f"[OnionSearch] [safe_request] Connection refused to {url[:100]}... "
                        f"Retrying {retries}/{max_retries} after {wait_time}s"
                    )
                    time.sleep(wait_time)
                else:
                    loguru_logger.error(
                        f"[OnionSearch] [safe_request] Failed to connect to {url[:100]}... "
                        f"after {max_retries + 1} attempts: {e}"
                    )
                    logger.error(f"✗ Failed to connect to {url} after {max_retries + 1} attempts: {e}")
                    raise
            else:
                loguru_logger.error(f"[OnionSearch] [safe_request] Connection error to {url[:100]}...: {e}")
                logger.error(f"✗ Connection error to {url}: {e}")
                raise
        
        except requests.exceptions.Timeout as e:
            last_exception = e
            retries += 1
            if retries <= max_retries:
                wait_time = min(2 ** retries, 10)
                loguru_logger.warning(
                    f"[OnionSearch] [safe_request] Timeout for {url[:100]}... "
                    f"Retrying {retries}/{max_retries} after {wait_time}s"
                )
                time.sleep(wait_time)
            else:
                loguru_logger.error(
                    f"[OnionSearch] [safe_request] Request timeout for {url[:100]}... "
                    f"after {max_retries + 1} attempts"
                )
                logger.error(f"✗ Request timeout for {url} after {max_retries + 1} attempts")
                raise
        
        except requests.exceptions.RequestException as e:
            last_exception = e
            loguru_logger.error(f"[OnionSearch] [safe_request] Request error for {url[:100]}...: {e}")
            logger.error(f"✗ Request error for {url}: {e}")
            raise
        
        except Exception as e:
            last_exception = e
            loguru_logger.error(
                f"[OnionSearch] [safe_request] Unexpected error for {url[:100]}...: "
                f"{type(e).__name__}: {e}"
            )
            logger.error(f"✗ Unexpected error for {url}: {type(e).__name__}: {e}")
            raise
    
    # If we get here, all retries failed
    if last_exception:
        raise last_exception


def link_finder(engine_str: str, data_obj, debug: bool = False) -> List[Dict[str, str]]:
    
    found_links = []
    name = ""
    link = ""

    def add_link():
        found_links.append({"engine": engine_str, "name": name, "link": link})
        if debug:
            loguru_logger.debug(
                f"[OnionSearch] [link_finder] [{engine_str}] Added link - "
                f"name='{name[:50]}', link='{link[:100]}'"
            )

    if engine_str == "ahmia":
        # Try multiple selectors as Ahmia structure may have changed
        selectors = [
            'li.result h4 a',
            '.result h4 a',
            'div.result h4 a',
            'li.result a',
        ]
        found = False
        total_elements = 0
        parsed_count = 0
        rejected_count = 0
        
        for selector in selectors:
            results_elems = data_obj.select(selector)
            if results_elems:
                total_elements = len(results_elems)
                if debug:
                    loguru_logger.debug(f"[OnionSearch] [link_finder] [Ahmia] Using selector '{selector}' found {len(results_elems)} elements")
                for idx, r in enumerate(results_elems):
                    try:
                        href = r.get('href', '')
                        if debug and idx < 3:
                            loguru_logger.debug(f"[OnionSearch] [link_finder] [Ahmia] Element {idx}: href='{href[:150]}'")
                        
                        if 'redirect_url=' in href:
                            name = clear(r.get_text())
                            link = href.split('redirect_url=')[1].split('&')[0]  # Handle additional params
                            
                            if debug and idx < 3:
                                loguru_logger.debug(
                                    f"[OnionSearch] [link_finder] [Ahmia] Element {idx}: "
                                    f"extracted link='{link[:100]}', name='{name[:50]}'"
                                )
                            
                            add_link()
                            parsed_count += 1
                            found = True
                        else:
                            rejected_count += 1
                            if debug and idx < 3:
                                loguru_logger.debug(f"[OnionSearch] [link_finder] [Ahmia] Element {idx}: Rejected - no 'redirect_url=' in href")
                    except (KeyError, IndexError, AttributeError) as e:
                        rejected_count += 1
                        if debug:
                            loguru_logger.debug(f"[OnionSearch] [link_finder] [Ahmia] Element {idx}: Error parsing - {e}")
                        continue
                if found:
                    break
        
        loguru_logger.debug(
            f"[OnionSearch] [link_finder] [Ahmia] Summary - "
            f"Total elements: {total_elements}, Parsed: {parsed_count}, Rejected: {rejected_count}, "
            f"Final links: {len(found_links)}"
        )
        
        if not found and debug:
            loguru_logger.debug("Ahmia: No results found with any selector")

    elif engine_str == "tor66":
        hr_tag = data_obj.find('hr')
        parsed_count = 0
        rejected_count = 0
        
        if hr_tag:
            all_b_tags = hr_tag.find_all_next('b')
            total_b_tags = len(all_b_tags)
            
            if debug:
                loguru_logger.debug(f"[OnionSearch] [link_finder] [Tor66] Found <hr> tag, processing {total_b_tags} <b> tags")
            
            for idx, i in enumerate(all_b_tags):
                try:
                    anchor = i.find('a')
                    # Fix: Check for href using get() instead of 'in' operator
                    if anchor and anchor.get('href'):
                        name = clear(anchor.get_text())
                        link = clear(anchor.get('href'))
                        
                        if debug and idx < 3:
                            loguru_logger.debug(
                                f"[OnionSearch] [link_finder] [Tor66] Element {idx}: "
                                f"href='{link[:100]}', name='{name[:50]}'"
                            )
                        
                        # Filter out service info and other non-result links
                        if link and '.onion' in link and '/serviceinfo/' not in link:
                            add_link()
                            parsed_count += 1
                        else:
                            rejected_count += 1
                            if debug and idx < 3:
                                reason = "no .onion" if '.onion' not in link else "serviceinfo" if '/serviceinfo/' in link else "empty link"
                                loguru_logger.debug(f"[OnionSearch] [link_finder] [Tor66] Element {idx}: Rejected - {reason}")
                    else:
                        rejected_count += 1
                        if debug and idx < 3:
                            loguru_logger.debug(f"[OnionSearch] [link_finder] [Tor66] Element {idx}: Rejected - no anchor or href")
                except (KeyError, AttributeError, TypeError) as e:
                    rejected_count += 1
                    if debug:
                        loguru_logger.debug(f"[OnionSearch] [link_finder] [Tor66] Element {idx}: Error parsing - {e}")
                    continue
            
            loguru_logger.debug(
                f"[OnionSearch] [link_finder] [Tor66] Summary - "
                f"Total <b> tags: {total_b_tags}, Parsed: {parsed_count}, Rejected: {rejected_count}, "
                f"Final links: {len(found_links)}"
            )
        else:
            if debug:
                loguru_logger.debug("Tor66: No <hr> tag found in results")

    return found_links


def ahmia(
    searchstr: str,
    proxies: Dict[str, str],
    timeout: Optional[int] = None,
    max_retries: int = 2,
    debug: bool = False
) -> List[Dict[str, str]]:
    
    engine_start = time.time()
    loguru_logger.info(f"[OnionSearch] [Ahmia] Starting search for: {searchstr}")
    results = []
    # Ahmia requires a CSRF token from the search form
    ahmia_base = ENGINES['ahmia']
    
    try:
        # First, get the search page to extract the CSRF token
        loguru_logger.debug(f"[OnionSearch] [Ahmia] Getting search page to extract CSRF token")
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
        
        loguru_logger.debug(f"[OnionSearch] [Ahmia] Requesting search with CSRF token")
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
        
        engine_time = time.time() - engine_start
        
        # Debug logging: show sample results
        if results:
            sample_results = results[:5]
            loguru_logger.debug(
                f"[OnionSearch] [Ahmia] Sample results (first 5): {sample_results}"
            )
            # Log sample links
            sample_links = [r.get('link', '')[:100] for r in sample_results]
            loguru_logger.debug(
                f"[OnionSearch] [Ahmia] Sample links: {sample_links}"
            )
        else:
            loguru_logger.debug("[OnionSearch] [Ahmia] No results extracted from page")
        
        loguru_logger.info(
            f"[OnionSearch] [Ahmia] Found {len(results)} results in {engine_time:.2f}s for query: {searchstr}"
        )
        if debug:
            logger.debug(f"Ahmia: Found {len(results)} results")
    except Exception as e:
        engine_time = time.time() - engine_start
        loguru_logger.error(
            f"[OnionSearch] [Ahmia] Failed to fetch results after {engine_time:.2f}s: {e}",
            exc_info=debug
        )
        logger.error(f"Ahmia: Failed to fetch results: {e}")
        if debug:
            import traceback
            logger.debug(traceback.format_exc())

    return results


def tor66(
    searchstr: str,
    proxies: Dict[str, str],
    timeout: Optional[int] = None,
    max_retries: int = 2,
    max_pages: int = 30,
    debug: bool = False
) -> List[Dict[str, str]]:
    
    engine_start = time.time()
    loguru_logger.info(f"[OnionSearch] [Tor66] Starting search for: {searchstr} (max_pages={max_pages})")
    results = []
    tor66_url = ENGINES['tor66'] + "/search?q={}&sorttype=rel&page={}"
    
    try:
        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()

            url = tor66_url.format(quote(searchstr), 1)
            loguru_logger.debug(f"[OnionSearch] [Tor66] Requesting page 1: {url[:100]}...")
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
                loguru_logger.info(
                    f"[OnionSearch] [Tor66] Found {nb_res} total results, "
                    f"will fetch {page_number} pages"
                )

            results = link_finder("tor66", soup, debug=debug)
            loguru_logger.debug(f"[OnionSearch] [Tor66] Page 1: Found {len(results)} results")

            for n in range(2, page_number + 1):
                try:
                    url = tor66_url.format(quote(searchstr), n)
                    loguru_logger.debug(f"[OnionSearch] [Tor66] Requesting page {n}/{page_number}")
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
                    loguru_logger.debug(f"[OnionSearch] [Tor66] Page {n}: Found {len(ret)} results")
                    results.extend(ret)
                except (requests.exceptions.RequestException, ConnectionError) as e:
                    loguru_logger.warning(
                        f"[OnionSearch] [Tor66] Error fetching page {n}/{page_number}: {e}"
                    )
                    logger.warning(f"Tor66: Error fetching page {n}: {e}")
                    if debug:
                        import traceback
                        logger.debug(traceback.format_exc())
                    break  # Stop if we hit an error on subsequent pages

    except Exception as e:
        engine_time = time.time() - engine_start
        loguru_logger.error(
            f"[OnionSearch] [Tor66] Failed to fetch results after {engine_time:.2f}s: {e}",
            exc_info=debug
        )
        logger.error(f"Tor66: Failed to fetch results: {e}")
        if debug:
            import traceback
            logger.debug(traceback.format_exc())
    
    engine_time = time.time() - engine_start
    
    # Debug logging: show sample results
    if results:
        sample_results = results[:5]
        loguru_logger.debug(
            f"[OnionSearch] [Tor66] Sample results (first 5): {sample_results}"
        )
        # Log sample links
        sample_links = [r.get('link', '')[:100] for r in sample_results]
        loguru_logger.debug(
            f"[OnionSearch] [Tor66] Sample links: {sample_links}"
        )
    else:
        loguru_logger.debug("[OnionSearch] [Tor66] No results extracted")
    
    loguru_logger.info(
        f"[OnionSearch] [Tor66] Found {len(results)} total results in {engine_time:.2f}s for query: {searchstr}"
    )

    return results


def search_all_engines(
    searchstr: str,
    proxies: Dict[str, str],
    engines: List[str] = None,
    timeout: Optional[int] = None,
    max_retries: int = 2,
    max_pages: int = 5,
    debug: bool = False
) -> List[str]:
    
    search_start = time.time()
    if engines is None:
        engines = ['ahmia', 'tor66']
    
    # Enforce minimum timeout of 300 seconds
    if timeout is not None and timeout < 300:
        loguru_logger.warning(
            f"[OnionSearch] [search_all_engines] Timeout {timeout}s is less than minimum 300s, "
            f"setting to 300s"
        )
        timeout = 300
    
    loguru_logger.info(
        f"[OnionSearch] [search_all_engines] Starting search across {len(engines)} engines: {engines} "
        f"for query: {searchstr} (timeout={timeout}s, max_pages={max_pages})"
    )
    
    all_results = []
    engine_functions = {
        'ahmia': ahmia,
        'tor66': tor66,
    }
    
    for engine_name in engines:
        if engine_name not in engine_functions:
            loguru_logger.warning(f"[OnionSearch] [search_all_engines] Unknown engine: {engine_name}, skipping")
            logger.warning(f"Unknown engine: {engine_name}, skipping")
            continue
        
        try:
            engine_start = time.time()
            loguru_logger.debug(f"[OnionSearch] [search_all_engines] Searching {engine_name} for: {searchstr}")
            logger.debug(f"Searching {engine_name} for: {searchstr}")
            engine_func = engine_functions[engine_name]
            
            # Call engine function with appropriate parameters
            if engine_name == 'ahmia':
                results = engine_func(searchstr, proxies, timeout, max_retries, debug)
            else:
                results = engine_func(searchstr, proxies, timeout, max_retries, max_pages, debug)
            
            engine_time = time.time() - engine_start
            
            # Debug: log raw results before adding
            loguru_logger.debug(
                f"[OnionSearch] [search_all_engines] {engine_name}: Raw results count: {len(results)}"
            )
            if results:
                sample_raw = results[:3]
                loguru_logger.debug(
                    f"[OnionSearch] [search_all_engines] {engine_name}: Sample raw results: {sample_raw}"
                )
            
            all_results.extend(results)
            loguru_logger.info(
                f"[OnionSearch] [search_all_engines] {engine_name}: Found {len(results)} results "
                f"in {engine_time:.2f}s"
            )
            logger.info(f"{engine_name}: Found {len(results)} results")
        except Exception as e:
            engine_time = time.time() - engine_start
            loguru_logger.error(
                f"[OnionSearch] [search_all_engines] {engine_name}: Error during search "
                f"after {engine_time:.2f}s: {e}",
                exc_info=debug
            )
            logger.error(f"{engine_name}: Error during search: {e}", exc_info=debug)
            continue
    
    # Extract unique URLs from results
    unique_urls = set()
    processed_count = 0
    rejected_count = 0
    duplicate_count = 0
    rejection_reasons = {}
    
    loguru_logger.info(f"[OnionSearch] [search_all_engines] Processing {len(all_results)} results for URL extraction")
    
    # Log sample results for debugging (always log, not just in debug mode)
    if all_results and len(all_results) > 0:
        sample_results = all_results[:3]
        loguru_logger.info(
            f"[OnionSearch] [search_all_engines] Sample results structure (first 3): {sample_results}"
        )
    
    for idx, result in enumerate(all_results):
        link = result.get('link', '').strip()
        processed_count += 1
        
        if not link:
            rejected_count += 1
            rejection_reasons['empty_link'] = rejection_reasons.get('empty_link', 0) + 1
            if idx < 5:  # Log first 5 rejections for debugging
                loguru_logger.debug(f"[OnionSearch] [search_all_engines] Result {idx}: Rejected - empty link, result={result}")
            continue
        
        # Check if .onion is in the link (not just endswith)
        if '.onion' not in link:
            rejected_count += 1
            rejection_reasons['no_onion'] = rejection_reasons.get('no_onion', 0) + 1
            if idx < 5:
                loguru_logger.debug(f"[OnionSearch] [search_all_engines] Result {idx}: Rejected - no .onion in link: '{link}'")
            continue
        
        # Extract and normalize the .onion URL
        try:
            # Handle different URL formats:
            # - http://something.onion/path?query
            # - https://something.onion
            # - something.onion
            # - something.onion/path
            
            # Extract the .onion domain part
            onion_match = re.search(r'([a-z2-7]{16,56}\.onion)', link, re.IGNORECASE)
            if not onion_match:
                rejected_count += 1
                rejection_reasons['invalid_onion_format'] = rejection_reasons.get('invalid_onion_format', 0) + 1
                if idx < 5:
                    loguru_logger.debug(f"[OnionSearch] [search_all_engines] Result {idx}: Rejected - invalid .onion format: '{link}'")
                continue
            
            onion_domain = onion_match.group(1).lower()
            
            # Normalize to http://domain.onion format
            normalized_link = f"http://{onion_domain}"
            
            # Check if this is a duplicate before adding
            if normalized_link in unique_urls:
                duplicate_count += 1
                if idx < 5:  # Log first 5 duplicates for debugging
                    loguru_logger.debug(
                        f"[OnionSearch] [search_all_engines] Result {idx}: Duplicate URL (already in set) - "
                        f"original='{link}', normalized='{normalized_link}'"
                    )
            else:
                unique_urls.add(normalized_link)
                if idx < 5:  # Log first 5 successful extractions
                    loguru_logger.debug(
                        f"[OnionSearch] [search_all_engines] Result {idx}: Extracted - "
                        f"original='{link}', normalized='{normalized_link}'"
                    )
                
        except Exception as e:
            rejected_count += 1
            rejection_reasons['extraction_error'] = rejection_reasons.get('extraction_error', 0) + 1
            loguru_logger.debug(
                f"[OnionSearch] [search_all_engines] Result {idx}: Error extracting URL from '{link}': {e}"
            )
            continue
    
    search_time = time.time() - search_start
    total_filtered = rejected_count + duplicate_count
    loguru_logger.info(
        f"[OnionSearch] [search_all_engines] Completed in {search_time:.2f}s. "
        f"Processed: {processed_count}, Accepted (unique): {len(unique_urls)}, "
        f"Rejected: {rejected_count}, Duplicates: {duplicate_count}, Total filtered: {total_filtered}. "
        f"Rejection reasons: {rejection_reasons}"
    )
    
    if unique_urls:
        sample_urls = list(unique_urls)[:5]
        loguru_logger.info(
            f"[OnionSearch] [search_all_engines] Sample extracted URLs (first 5): {sample_urls}"
        )
    else:
        loguru_logger.warning(
            f"[OnionSearch] [search_all_engines] WARNING: Extracted 0 URLs from {processed_count} results. "
            f"Rejection breakdown: {rejection_reasons}"
        )
    
    logger.info(f"Total unique URLs found: {len(unique_urls)}")
    return list(unique_urls)


class DarkWebEngine:
    
    
    def __init__(
        self,
        proxy_host: Optional[str] = None,
        proxy_port: Optional[int] = None,
        proxy_type: Optional[str] = None
    ):
        
        self.proxy_host = proxy_host or settings.TOR_PROXY_HOST
        self.proxy_port = proxy_port or settings.TOR_PROXY_PORT
        self.proxy_type = proxy_type or settings.TOR_PROXY_TYPE
        
        self.proxies = {
            "http": f"{self.proxy_type}://{self.proxy_host}:{self.proxy_port}",
        }
        
        # Get configured engines (default: ahmia, tor66)
        self.engines = settings.ONIONSEARCH_ENGINES
        # Enforce minimum timeout of 300 seconds
        if settings.ONIONSEARCH_TIMEOUT is not None and settings.ONIONSEARCH_TIMEOUT < 300:
            loguru_logger.warning(
                f"[DarkWebEngine] Timeout {settings.ONIONSEARCH_TIMEOUT}s is less than minimum 300s, "
                f"setting to 300s"
            )
            self.timeout = 300
        else:
            self.timeout = settings.ONIONSEARCH_TIMEOUT
        self.max_pages = settings.ONIONSEARCH_MAX_PAGES
        
        timeout_str = f"{self.timeout}s" if self.timeout is not None else "no timeout"
        loguru_logger.info(
            f"[DarkWebEngine] Initialized with proxy={self.proxy_type}://{self.proxy_host}:{self.proxy_port}, "
            f"engines={self.engines}, timeout={timeout_str}, max_pages={self.max_pages}"
        )
    
    def discover_urls(self, keywords: Optional[List[str]] = None) -> List[str]:
        
        discovery_start = time.time()
        
        # Require keywords - no fallback terms
        if not keywords or len(keywords) == 0:
            loguru_logger.error("[DarkWebEngine] No keywords provided. Keywords are required for discovery.")
            raise ValueError("Keywords are required for dark web discovery. No default fallback terms.")
        
        # Clean and validate keywords
        search_queries = [kw.strip() for kw in keywords if kw.strip()]
        
        if not search_queries:
            loguru_logger.error("[DarkWebEngine] No valid search queries provided after cleaning")
            raise ValueError("No valid keywords provided after cleaning. Please provide at least one keyword.")
        
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

