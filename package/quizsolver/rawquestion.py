import json
from .rawanswer import RawAnswer
from .common import RawQuestionType,  hash_string, xor_hash_bytes
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .question import Question


class RawQuestion:
    def __init__(self, *, quiz_question: dict, parent_question: 'Question'):
        """
        Initialize a RawQuestion from a dictionary value.
        Args:
            value (dict): Dictionary containing question data.
        """
        # load question properties
        self._original_value: dict = quiz_question
        self.parent_question: 'Question' = parent_question
        self.question_text: str = quiz_question.get("question", "")
        self.type: RawQuestionType = RawQuestionType(quiz_question.get("type", "chooseOne"))
        # compute raw hash of the question
        self.raw_hash_bytes: bytes = hash_string(self.question_text + self.type.value)
        self.raw_hash_str: str = self.raw_hash_bytes.hex()
        # load answers and check that each answer is different
        received_raw_answers = quiz_question.get("answers", [])
        if not received_raw_answers or len(received_raw_answers) == 0:
            raise ValueError("A question must have at least one answer.")
        self.raw_answers: list[RawAnswer] = []
        # each answer must be different
        seen_answer_hashes = set()
        for raw_answer in received_raw_answers:
            self.raw_answers.append(RawAnswer(quiz_answer=raw_answer))
        # create uid
        self.uid_bytes: bytes = self._compute_uid()
        self.uid: str = self.uid_bytes.hex()
        # set parent question and compute answer uids
        for raw_answer in self.raw_answers:
            if raw_answer.raw_hash_bytes in seen_answer_hashes:
                raise ValueError("Duplicate answer detected in a question:\n " +
                                  json.dumps(quiz_question, indent=4))
            seen_answer_hashes.add(raw_answer.raw_hash_bytes)
            raw_answer.parent_question = self
            raw_answer.uid_bytes = xor_hash_bytes(self.uid_bytes, raw_answer.raw_hash_bytes)
            raw_answer.uid = raw_answer.uid_bytes.hex()

    def _compute_uid(self):
        """
        Compute a unique identifier for the raw question based on its content.
        Returns: UID string
        """
        combined_hash = self.raw_hash_bytes
        for raw_answer in self.raw_answers:
            combined_hash = xor_hash_bytes(combined_hash, raw_answer.raw_hash_bytes) 
        return combined_hash
    
    def to_dict(self):
        """
        Get dictionary representation of the raw question.
        Returns: Dictionary with raw question details and answers.
        """
        return self._original_value