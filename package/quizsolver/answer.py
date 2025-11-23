import random
import math
import json
import time
import argparse
from .common import hash_string
from .rawanswer import RawAnswer

class Answer:
    def __init__(self, *, raw_answers: list[RawAnswer]):
        """
        Initialize an Answer with its raw answers.
        Args:
            raw_answers (list[RawAnswer]): List of RawAnswer objects associated with this answer.
        """
        self.raw_answers = raw_answers
        self.is_correct: bool| None = None
        # custom data for strategies
        self.data: dict = {}
    
    # def duplicate(self) -> 'Answer':
    #     """
    #     Create a duplicate of the answer with the same properties.
    #     Returns: A new Answer object with copied attributes.
    #     """
    #     new_answer = Answer(raw_answers=self.raw_answers)
    #     new_answer.is_correct = self.is_correct
    #     return new_answer

    @property
    def answer_text(self) -> str:
        """
        Get the text of the answer.
        Returns: Answer text as a string.
        """
        result = [raw_answer.answer_text for raw_answer in self.raw_answers]
        return "\n".join(result)
    
    def to_dict(self) -> dict:
        """
        Get dictionary representation of the answer.
        Returns: Dictionary with answer details.
        """
        return {
            "answers": [raw_answer.to_dict() for raw_answer in self.raw_answers],
            "is_correct": self.is_correct,
            "data": self.data
        }
    
    def to_response_list_of_raw_answers(self, *, strategy_name: str,
                                        most_probable_key: str = "most_probable") -> list[dict]:
        """
        Get list of raw answer dictionaries for response.
        Returns: List of dictionaries representing raw answers.
        """
        result = []
        for raw_answer in self.raw_answers:
            result.append(raw_answer.to_dict())
            # Add correct field based on most probable answer for the strategy
            if strategy_name in self.data:
                most_probable = self.data[strategy_name].get(most_probable_key, None)
                result[-1]["correct"] = most_probable
            else:
                raise ValueError("Cannot determine correctness of the answer.")
        return result