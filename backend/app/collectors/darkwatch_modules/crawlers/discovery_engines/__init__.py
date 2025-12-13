"""
Discovery Engines Module

Provides URL discovery from various sources.
"""

from .onionsearch import DarkWebEngine  # DarkWebEngine is now in onionsearch.py

__all__ = [
    'DarkWebEngine'
]
