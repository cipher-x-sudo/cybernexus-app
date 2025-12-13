"""
Discovery Engines Module

Provides URL discovery from various sources.
"""

from .gist_engine import GistEngine
from .security_news_engine import SecurityNewsEngine
from .onionsearch import DarkWebEngine  # DarkWebEngine is now in onionsearch.py
from .search_engine import SearchEngine
from .pastebin_engine import PastebinEngine

__all__ = [
    'GistEngine',
    'SecurityNewsEngine',
    'DarkWebEngine',
    'SearchEngine',
    'PastebinEngine'
]
