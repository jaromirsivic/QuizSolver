from enum import Enum
from .common import hash_string
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .quizsolver import RawQuestion



class RawAnswer:
    def __init__(self, *, quiz_answer: dict):
        """
        Initialize a RawAnswer object from a dictionary.
        Args:
            value (dict): A dictionary containing answer properties.
        """
        # load answer properties
        self._original_value: dict = quiz_answer
        self.answer_text: str = quiz_answer.get("answer", "")
        # compute raw hash
        self.raw_hash_bytes: bytes = hash_string(self.answer_text)
        self.raw_hash_str: str = self.raw_hash_bytes.hex()
        # create uid and link to parent question
        # uid and link to parent question will be set in RawQuestion
        self.uid_bytes: bytes
        self.uid: str
        self.parent_question: 'RawQuestion'

    def to_dict(self):
        """
        Get dictionary representation of the raw answer.
        Returns: Dictionary with raw answer details.
        """
        return self._original_value