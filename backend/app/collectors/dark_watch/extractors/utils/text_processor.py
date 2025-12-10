"""
Text Processing Utility

Cleans and extracts text from HTML content.
Adapted from freshonions-torscraper.
"""

from bs4 import BeautifulSoup
from typing import Optional


def extract_text_from_html(html_content: bytes) -> str:
    """
    Extract text from HTML content.
    
    Args:
        html_content: HTML content as bytes
        
    Returns:
        Cleaned text content
    """
    soup = BeautifulSoup(html_content, features="lxml")
    
    # Remove script and style elements
    for s in soup(['script', 'style']):
        s.decompose()
    
    return ' '.join(soup.stripped_strings)


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text.strip()
