"""
Email Utility

Extracts email addresses from text.
Adapted from freshonions-torscraper.
"""

import re
from typing import List


REGEX = re.compile(r'\b[a-zA-Z0-9_.+-]{1,50}@[a-zA-Z0-9-]{1,50}\.[a-zA-Z0-9-.]{1,50}[a-zA-Z0-9]\b')
REGEX_ALL = re.compile(r'^[a-zA-Z0-9_.+-]{1,50}@[a-zA-Z0-9-]{1,50}\.[a-zA-Z0-9-.]{1,50}[a-zA-Z0-9]$')


def is_valid_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid format, False otherwise
    """
    return bool(re.match(REGEX_ALL, email))


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to search
        
    Returns:
        List of email addresses found
    """
    emails = REGEX.findall(text)
    # Filter valid emails
    valid_emails = [email for email in emails if is_valid_email(email)]
    return list(set(valid_emails))  # Return unique emails
