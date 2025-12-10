"""
Utility Modules for Entity Extraction

Provides utilities for extracting emails, bitcoin addresses, and other entities.
"""

from .bitcoin_util import extract_bitcoin_addresses, is_valid_bitcoin
from .email_util import extract_emails
from .portscanner import scan_ports
from .text_processor import clean_text, extract_text_from_html
from .language_detector import detect_language

__all__ = [
    'extract_bitcoin_addresses',
    'is_valid_bitcoin',
    'extract_emails',
    'scan_ports',
    'clean_text',
    'extract_text_from_html',
    'detect_language'
]
