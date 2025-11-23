from hashlib import sha3_256
from itertools import combinations, chain
from enum import Enum

epsilon = 0.0000001

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

def inverse_square_likelyhood(*, value: float, min: float, max: float, 
                              min_likelyhood: float, max_likelyhood: float) -> float:
    """
    Calculate an inverse square likelyhood for a given value within a range.
    Args:
        min (float): The minimum value of the range.
        max (float): The maximum value of the range.
        min_likelyhood (float): The likelyhood corresponding to the maximum value.
        max_likelyhood (float): The likelyhood corresponding to the minimum value.
        value (float): The value for which to calculate the likelyhood.
    Returns:
        float: The calculated likelyhood.
    """
    if min == max:
        return max_likelyhood
    if min > max:
        raise ValueError(f'"min" must be lower than "max"')
    if min_likelyhood > max_likelyhood:
        raise ValueError(f'"min_likelyhood" must be lower than "max_likelyhood"')
    # Calculate the likelyhood
    min_max_diff = max - min
    likelyhood_diff = max_likelyhood - min_likelyhood
    value_projected_into_0_1_range = (value - min) / min_max_diff
    inverted_value_projected_into_0_1_range = 1 - value_projected_into_0_1_range
    inverted_value_projected_into_0_1_range_squared = inverted_value_projected_into_0_1_range ** 2
    likelyhood = (inverted_value_projected_into_0_1_range_squared * likelyhood_diff) + min_likelyhood
    return likelyhood

def minmax(values, key) -> tuple[float, object, float, object]:
    """
    Find the minimum and maximum values in a list based on a key function.
    Args:
        values (list): The list of values to evaluate.
        key (function): A function that takes a value and returns a comparable key.
    Returns:
        tuple: A tuple containing the minimum key value, the corresponding value,
               the maximum key value, and the corresponding value.
    """
    min_value = float('inf')
    min_index = -1
    max_value = float('-inf')
    max_index = -1
    for i, v in enumerate(values):
        k = key(v)
        if k < min_value:
            min_value = k
            min_index = i
        if k > max_value:
            max_value = k
            max_index = i
    return min_value, values[min_index], max_value, values[max_index]