"""Browser capture and automation service.

This module provides browser automation and page capture functionality using Playwright.
Does not use custom DSA structures.

This module does not use custom DSA concepts from app.core.dsa.
"""

import asyncio
import json
import base64
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import tempfile
import os
from io import BytesIO

from playwright.async_api import async_playwright, Browser, Page, Route, Request, Response
from loguru import logger


_thread_local = threading.local()


class BrowserCaptureService:
    def __init__(self):
        pass
    
    def _get_thread_local_storage(self):
        if not hasattr(_thread_local, 'browser'):
            _thread_local.browser = None
            _thread_local.playwright = None
            _thread_local.initialized = False
        return _thread_local
    
    async def initialize(self):
        storage = self._get_thread_local_storage()
        
        if storage.initialized:
            try:
                if storage.browser and storage.browser.is_connected():
                    return
            except Exception:
                storage.initialized = False
                storage.browser = None
                storage.playwright = None
        
        try:
            storage.playwright = await async_playwright().start()
            storage.browser = await storage.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                ]
            )
            storage.initialized = True
            logger.info(f"[BrowserCapture] Playwright browser initialized for thread {threading.get_ident()}")
        except Exception as e:
            logger.error(f"[BrowserCapture] Failed to initialize browser: {e}")
            storage.initialized = False
            storage.browser = None
            storage.playwright = None
            raise
    
    async def close(self):
        storage = self._get_thread_local_storage()
        
        try:
            if storage.browser:
                try:
                    await storage.browser.close()
                except Exception as e:
                    logger.warning(f"[BrowserCapture] Error closing browser: {e}")
                storage.browser = None
            
            if storage.playwright:
                try:
                    await storage.playwright.stop()
                except Exception as e:
                    logger.warning(f"[BrowserCapture] Error stopping playwright: {e}")
                storage.playwright = None
            
            storage.initialized = False
            logger.info(f"[BrowserCapture] Browser closed for thread {threading.get_ident()}")
        except Exception as e:
            logger.error(f"[BrowserCapture] Error during cleanup: {e}")
    
    def _get_browser(self) -> Optional[Browser]:
        storage = self._get_thread_local_storage()
        return storage.browser
    
    async def capture_page(
        self,
        url: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        storage = self._get_thread_local_storage()
        if not storage.initialized:
            await self.initialize()
        
        browser = self._get_browser()
        if not browser:
            raise RuntimeError("Browser not initialized")
        
        options = options or {}
        wait_until = options.get('wait_until', 'networkidle')
        timeout = options.get('timeout', 30000)
        full_page = options.get('full_page', True)
        viewport_width = options.get('viewport_width', 1920)
        viewport_height = options.get('viewport_height', 1080)
        user_agent = options.get('user_agent', None)
        
        context = None
        page = None
        
        try:
            context_options = {
                'viewport': {'width': viewport_width, 'height': viewport_height},
                'ignore_https_errors': True,
            }
            if user_agent:
                context_options['user_agent'] = user_agent
            
            context = await browser.new_context(**context_options)
            
            page = await context.new_page()
            
            har_entries = []
            redirect_chain = []
            
            def handle_request(request: Request):
                har_entries.append({
                    'request': request,
                    'timestamp': datetime.now().isoformat(),
                })
            
            def handle_response(response: Response):
                for entry in har_entries:
                    if entry['request'].url == response.url:
                        entry['response'] = response
                        break
            
            def handle_request_finished(request: Request):
                pass
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            logger.info(f"[BrowserCapture] Navigating to {url}")
            response = await page.goto(
                url,
                wait_until=wait_until,
                timeout=timeout
            )
            
            if response:
                redirect_chain.append(response.url)
                if hasattr(response, 'request') and response.request.redirected_from:
                    redirect_chain.insert(0, response.request.url)
            
            await asyncio.sleep(2)
            
            final_url = page.url
            title = await page.title()
            
            logger.info(f"[BrowserCapture] Capturing screenshot")
            screenshot_bytes = await page.screenshot(
                full_page=full_page,
                type='png'
            )
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            

            logger.info(f"[BrowserCapture] Building HAR file")
            har = self._build_har(url, final_url, page, har_entries, redirect_chain)
            
            result = {
                'screenshot': screenshot_b64,
                'har': har,
                'final_url': final_url,
                'title': title,
                'redirect_chain': redirect_chain,
                'capture_time': datetime.now().isoformat(),
                'viewport': {
                    'width': viewport_width,
                    'height': viewport_height
                }
            }
            
            logger.info(f"[BrowserCapture] Capture completed for {url}")
            return result
            
        except Exception as e:
            logger.error(f"[BrowserCapture] Error capturing {url}: {e}")
            raise
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
    
    def _build_har(
        self,
        initial_url: str,
        final_url: str,
        page: Page,
        har_entries: List[Dict],
        redirect_chain: List[str]
    ) -> Dict[str, Any]:
        har = {
            'version': '1.2',
            'creator': {
                'name': 'CyberNexus Browser Capture',
                'version': '1.0'
            },
            'browser': {
                'name': 'Chromium',
                'version': '120.0'
            },
            'pages': [
                {
                    'startedDateTime': datetime.now().isoformat(),
                    'id': 'page_1',
                    'title': '',
                    'pageTimings': {
                        'onContentLoad': -1,
                        'onLoad': -1
                    }
                }
            ],
            'entries': []
        }
        
        for entry in har_entries:
            request = entry.get('request')
            response = entry.get('response')
            
            if not request:
                continue
            
            har_request = {
                'method': request.method,
                'url': request.url,
                'httpVersion': 'HTTP/1.1',
                'headers': [
                    {'name': name, 'value': value}
                    for name, value in request.headers.items()
                ],
                'queryString': [],
                'cookies': [],
                'headersSize': -1,
                'bodySize': -1
            }
            
            har_response = {
                'status': response.status if response else 0,
                'statusText': response.status_text if response else '',
                'httpVersion': 'HTTP/1.1',
                'headers': [
                    {'name': name, 'value': value}
                    for name, value in (response.headers.items() if response else {})
                ],
                'cookies': [],
                'content': {
                    'size': -1,
                    'mimeType': response.headers.get('content-type', '') if response else '',
                    'text': ''
                },
                'redirectURL': '',
                'headersSize': -1,
                'bodySize': -1
            }
            
            har_timings = {
                'blocked': -1,
                'dns': -1,
                'connect': -1,
                'send': 0,
                'wait': 0,
                'receive': 0,
                'ssl': -1
            }
            
            har_entry = {
                'pageref': 'page_1',
                'startedDateTime': entry.get('timestamp', datetime.now().isoformat()),
                'time': sum(v for v in har_timings.values() if v > 0),
                'request': har_request,
                'response': har_response,
                'cache': {},
                'timings': har_timings
            }
            
            har['entries'].append(har_entry)
        
        return har
    
    async def capture_multiple(
        self,
        urls: List[str],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        
        storage = self._get_thread_local_storage()
        if not storage.initialized:
            await self.initialize()
        
        tasks = [self.capture_page(url, options) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            url: result if not isinstance(result, Exception) else {'error': str(result)}
            for url, result in zip(urls, results)
        }


_browser_capture_service: Optional[BrowserCaptureService] = None


def get_browser_capture_service() -> BrowserCaptureService:
    global _browser_capture_service
    if _browser_capture_service is None:
        _browser_capture_service = BrowserCaptureService()
    return _browser_capture_service


async def cleanup_all_browser_instances():
    logger.info("[BrowserCapture] Cleanup requested for all browser instances")

