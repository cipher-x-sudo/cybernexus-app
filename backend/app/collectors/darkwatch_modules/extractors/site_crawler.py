

import requests
import logging
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from app.config import settings
from .utils import (
    extract_emails,
    extract_bitcoin_addresses,
    extract_text_from_html,
    detect_language,
    scan_ports,
    find_interesting_paths_in_content
)


logger = logging.getLogger(__name__)


def crawl_onion_site(
    url: str,
    proxy_host: Optional[str] = None,
    proxy_port: Optional[int] = None,
    proxy_type: Optional[str] = None,
    timeout: Optional[int] = None,
    max_depth: int = 1
) -> Dict[str, Any]:
    
    proxy_host = proxy_host or settings.TOR_PROXY_HOST
    proxy_port = proxy_port or settings.TOR_PROXY_PORT
    proxy_type = proxy_type or settings.TOR_PROXY_TYPE
    timeout = timeout or settings.TOR_TIMEOUT
    
    proxies = {
        "http": f"{proxy_type}://{proxy_host}:{proxy_port}",
    }
    

    if not url.startswith('http://') and not url.startswith('https://'):
        url = f"http://{url}"
    
    result = {
        "url": url,
        "status": "unknown",
        "title": None,
        "content": None,
        "text": None,
        "language": "unknown",
        "emails": [],
        "bitcoin_addresses": [],
        "interesting_paths": [],
        "open_ports": [],
        "links": [],
        "error": None
    }
    
    try:
        logger.info(f"Crawling {url}")
        session = requests.session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        response = session.get(
            url,
            proxies=proxies,
            headers=headers,
            timeout=timeout
        )
        
        result["status"] = "online" if response.status_code == 200 else "offline"
        result["status_code"] = response.status_code
        
        if response.status_code == 200:

            soup = BeautifulSoup(response.content, features="lxml")
            title_tag = soup.find('title')
            if title_tag:
                result["title"] = title_tag.get_text().strip()
            

            result["text"] = extract_text_from_html(response.content)
            result["content"] = response.text
            

            if result["text"]:
                result["language"] = detect_language(result["text"])
            

            result["emails"] = extract_emails(result["text"])
            result["bitcoin_addresses"] = extract_bitcoin_addresses(result["text"])
            

            result["interesting_paths"] = list(
                find_interesting_paths_in_content(result["content"], url)
            )
            

            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href:

                    if href.startswith('http://') or href.startswith('https://'):
                        links.append(href)
                    elif href.startswith('/'):
                        links.append(f"{url.rstrip('/')}{href}")
                    elif '.onion' in href:
                        links.append(href)
            result["links"] = list(set(links))
            


            hostname = url.replace('http://', '').replace('https://', '').split('/')[0]

    
    except requests.exceptions.ConnectionError as e:
        logger.debug(f"Connection error for {url}: {e}")
        result["status"] = "offline"
        result["error"] = str(e)
    except requests.exceptions.Timeout as e:
        logger.debug(f"Timeout for {url}: {e}")
        result["status"] = "timeout"
        result["error"] = str(e)
    except Exception as e:
        logger.error(f"Error crawling {url}: {e}")
        result["status"] = "error"
        result["error"] = str(e)
    
    return result


def extract_entities(content: str, url: str) -> List[Dict[str, Any]]:
    
    entities = []
    

    emails = extract_emails(content)
    for email in emails:
        entities.append({
            "type": "email",
            "value": email,
            "source_url": url
        })
    

    bitcoin_addrs = extract_bitcoin_addresses(content)
    for addr in bitcoin_addrs:
        entities.append({
            "type": "bitcoin",
            "value": addr,
            "source_url": url
        })
    
    return entities
