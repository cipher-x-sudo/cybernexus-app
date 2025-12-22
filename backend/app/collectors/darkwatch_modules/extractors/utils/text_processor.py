

from bs4 import BeautifulSoup
from typing import Optional


def extract_text_from_html(html_content: bytes) -> str:
    
    soup = BeautifulSoup(html_content, features="lxml")
    

    for s in soup(['script', 'style']):
        s.decompose()
    
    return ' '.join(soup.stripped_strings)


def clean_text(text: str) -> str:
    

    text = ' '.join(text.split())
    

    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text.strip()
