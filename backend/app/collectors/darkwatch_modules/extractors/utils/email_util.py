

import re
from typing import List


REGEX = re.compile(r'\b[a-zA-Z0-9_.+-]{1,50}@[a-zA-Z0-9-]{1,50}\.[a-zA-Z0-9-.]{1,50}[a-zA-Z0-9]\b')
REGEX_ALL = re.compile(r'^[a-zA-Z0-9_.+-]{1,50}@[a-zA-Z0-9-]{1,50}\.[a-zA-Z0-9-.]{1,50}[a-zA-Z0-9]$')


def is_valid_email(email: str) -> bool:
    
    return bool(re.match(REGEX_ALL, email))


def extract_emails(text: str) -> List[str]:
    
    emails = REGEX.findall(text)

    valid_emails = [email for email in emails if is_valid_email(email)]
    return list(set(valid_emails))  # Return unique emails
