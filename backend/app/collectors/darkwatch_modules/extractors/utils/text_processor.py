

from bs4 import BeautifulSoup
from typing import Optional


def extract_text_from_html(html_content: bytes) -> str:
    
    soup = BeautifulSoup(html_content, features="lxml")
    
    # Remove script and style elements
    for s in soup(['script', 'style']):
        s.decompose()
    
    return ' '.join(soup.stripped_strings)


def clean_text(text: str) -> str:
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text.strip()
