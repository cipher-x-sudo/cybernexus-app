

import re
from typing import List
from Crypto.Hash import SHA256


REGEX = re.compile(r'\b[13][a-zA-Z1-9]{26,34}\b')
REGEX_ALL = re.compile(r'^[13][a-zA-Z1-9]{26,34}$')

__b58chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
__b58base = len(__b58chars)


def b58decode(v, length):
    
    long_value = 0
    for (i, c) in enumerate(v[::-1]):
        long_value += __b58chars.find(c) * (__b58base**i)
    
    result = ''
    while long_value >= 256:
        div, mod = divmod(long_value, 256)
        result = chr(mod) + result
        long_value = div
    
    result = chr(long_value) + result
    
    nPad = 0
    for c in v:
        if c == __b58chars[0]:
            nPad += 1
        else:
            break
    
    result = chr(0)*nPad + result
    if length is not None and len(result) != length:
        return None
    
    return result


def is_valid_bitcoin(addr: str) -> bool:
    
    addr = addr.strip()
    if not re.match(REGEX_ALL, addr):
        return False
    
    bin_addr = b58decode(addr, 25)
    if bin_addr is None:
        return False
    
    version = bin_addr[0]
    checksum = bin_addr[-4:]
    vh160 = bin_addr[:-4]  # Version plus hash160
    
    h3 = SHA256.new(SHA256.new(vh160).digest()).digest()
    if h3[0:4] == checksum:
        return True
    return False


def extract_bitcoin_addresses(text: str) -> List[str]:
    
    addresses = []
    matches = REGEX.findall(text)
    
    for match in matches:
        if is_valid_bitcoin(match):
            addresses.append(match)
    
    return list(set(addresses))  # Return unique addresses
