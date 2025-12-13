"""
Discovery Engines Module

Provides URL discovery from various sources.
"""

from .gist_engine import GistEngine
from .onionsearch import DarkWebEngine  # DarkWebEngine is now in onionsearch.py

__all__ = [
    'GistEngine',
    'DarkWebEngine'
]
