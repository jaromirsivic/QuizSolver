from hashlib import sha3_256
from itertools import combinations, chain
from enum import Enum

epsilon = 0.000001

class RawQuestionType(Enum):
    CHOOSE_ONE = "chooseOne"
    CHOOSE_ONE_OR_MORE = "chooseOneOrMore"
    CHOOSE_ZERO_OR_MORE = "chooseZeroOrMore"

def powerset(iterable):
    """Generate the powerset of the input iterable."""
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def hash_string(s: str) -> bytes:
    """Generate a SHA3-256 hash of the input string."""
    return sha3_256(s.encode('utf-8')).digest()
    

def xor_hex_strings(s1: str, s2: str) -> str:
    """XOR two hex strings of equal length."""
    if len(s1) != len(s2):
        raise ValueError("Hex strings must be of equal length to XOR.")
    b1 = bytes.fromhex(s1)
    b2 = bytes.fromhex(s2)
    xored = bytes(a ^ b for a, b in zip(b1, b2))
    return xored.hex()

def xor_hash_bytes(b1: bytes, b2: bytes) -> bytes:
    """XOR two byte sequences of equal length."""
    if len(b1) != len(b2):
        raise ValueError("Byte sequences must be of equal length to XOR.")
    return bytes(a ^ b for a, b in zip(b1, b2))