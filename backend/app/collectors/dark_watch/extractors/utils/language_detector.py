"""
Language Detection Utility

Detects language of text content.
Simplified version - can be enhanced with langdetect library.
"""

import re
from typing import Optional


# Common language patterns (simplified)
LANGUAGE_PATTERNS = {
    'en': [r'\bthe\b', r'\band\b', r'\bor\b', r'\bis\b'],
    'es': [r'\bel\b', r'\bla\b', r'\bde\b', r'\bque\b'],
    'fr': [r'\ble\b', r'\bla\b', r'\bde\b', r'\bet\b'],
    'de': [r'\bder\b', r'\bdie\b', r'\bdas\b', r'\bund\b'],
    'ru': [r'[а-яА-Я]'],
    'zh': [r'[\u4e00-\u9fff]'],
    'ar': [r'[\u0600-\u06FF]'],
}


def detect_language(text: str) -> str:
    """
    Detect language of text (simplified).
    
    Args:
        text: Text to analyze
        
    Returns:
        Language code (defaults to 'en')
    
    Note:
        This is a simplified implementation. For better accuracy,
        consider using the 'langdetect' library.
    """
    if not text or len(text) < 10:
        return 'unknown'
    
    text_lower = text.lower()
    scores = {}
    
    for lang, patterns in LANGUAGE_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            score += matches
        scores[lang] = score
    
    if scores:
        detected = max(scores, key=scores.get)
        if scores[detected] > 0:
            return detected
    
    # Default to English if no strong match
    return 'en'
