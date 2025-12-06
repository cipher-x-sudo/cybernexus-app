"""
Custom Database Layer

File-based persistence using custom DSA structures.
No external database dependencies.
"""

from .storage import Storage
from .indexer import Indexer
from .serializer import Serializer

__all__ = ["Storage", "Indexer", "Serializer"]


