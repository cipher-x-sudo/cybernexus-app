"""
Browser Capture Service

Provides real browser automation for page capture, screenshot generation,
and HAR file export using Playwright.
"""

import asyncio
import json
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import tempfile
import os
from io import BytesIO

from playwright.async_api import async_playwright, Browser, Page, Route, Request, Response
from loguru import logger


class BrowserCaptureService:
    """
    Service for capturing web pages using Playwright.
    
    Features:
    - Full page screenshot capture
    - HAR file generation from network traffic
    - JavaScript execution support
    - Redirect handling
    - Headless browser automation
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Playwright browser instance"""
        if self._initialized:
            return
        
        try:
            self.playwright = await async_playwright().start()
            # Launch browser with appropriate options
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                ]
            )
            self._initialized = True
            logger.info("[BrowserCapture] Playwright browser initialized")
        except Exception as e:
            logger.error(f"[BrowserCapture] Failed to initialize browser: {e}")
            raise
    
    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False
        logger.info("[BrowserCapture] Browser closed")
    
    async def capture_page(
        self,
        url: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Capture a web page with screenshot and HAR.
        
        Args:
            url: URL to capture
            options: Capture options:
                - wait_until: 'load' | 'domcontentloaded' | 'networkidle' | 'commit'
                - timeout: Timeout in milliseconds
                - full_page: Whether to capture full page screenshot
                - viewport_width: Viewport width
                - viewport_height: Viewport height
                - user_agent: Custom user agent
        
        Returns:
            Dictionary containing:
                - screenshot: Base64 encoded PNG image
                - har: HAR file content as dict
                - final_url: Final URL after redirects
                - title: Page title
                - redirect_chain: List of redirect URLs
                - capture_time: Capture timestamp
        """
        if not self._initialized:
            await self.initialize()
        
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
            # Create browser context
            context_options = {
                'viewport': {'width': viewport_width, 'height': viewport_height},
                'ignore_https_errors': True,
            }
            if user_agent:
                context_options['user_agent'] = user_agent
            
            context = await self.browser.new_context(**context_options)
            
            # Create page
            page = await context.new_page()
            
            # Track network requests for HAR
            har_entries = []
            redirect_chain = []
            
            def handle_request(request: Request):
                """Track request for HAR"""
                har_entries.append({
                    'request': request,
                    'timestamp': datetime.now().isoformat(),
                })
            
            def handle_response(response: Response):
                """Track response for HAR"""
                # Find matching request
                for entry in har_entries:
                    if entry['request'].url == response.url:
                        entry['response'] = response
                        break
            
            def handle_request_finished(request: Request):
                """Handle request completion"""
                pass
            
            # Set up network listeners
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            # Navigate to page
            logger.info(f"[BrowserCapture] Navigating to {url}")
            response = await page.goto(
                url,
                wait_until=wait_until,
                timeout=timeout
            )
            
            if response:
                redirect_chain.append(response.url)
                # Get redirect chain from response
                if hasattr(response, 'request') and response.request.redirected_from:
                    redirect_chain.insert(0, response.request.url)
            
            # Wait a bit for any late-loading resources
            await asyncio.sleep(2)
            
            # Get final URL and title
            final_url = page.url
            title = await page.title()
            
            # Capture screenshot
            logger.info(f"[BrowserCapture] Capturing screenshot")
            screenshot_bytes = await page.screenshot(
                full_page=full_page,
                type='png'
            )
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Build HAR file
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
        """Build HAR file from captured network traffic"""
        
        # HAR structure
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
        
        # Convert network entries to HAR format
        for entry in har_entries:
            request = entry.get('request')
            response = entry.get('response')
            
            if not request:
                continue
            
            # Build request object
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
            
            # Build response object
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
            
            # Build timings (simplified)
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
        """
        Capture multiple URLs in parallel.
        
        Args:
            urls: List of URLs to capture
            options: Capture options (same as capture_page)
        
        Returns:
            Dictionary mapping URL to capture result
        """
        if not self._initialized:
            await self.initialize()
        
        tasks = [self.capture_page(url, options) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            url: result if not isinstance(result, Exception) else {'error': str(result)}
            for url, result in zip(urls, results)
        }


# Global instance
_browser_capture_service: Optional[BrowserCaptureService] = None


def get_browser_capture_service() -> BrowserCaptureService:
    """Get global browser capture service instance"""
    global _browser_capture_service
    if _browser_capture_service is None:
        _browser_capture_service = BrowserCaptureService()
    return _browser_capture_service

