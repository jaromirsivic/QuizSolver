import random
from itertools import chain, combinations
from .common import powerset
from .answer import Answer
from .rawquestion import RawQuestion, RawQuestionType
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .quizsolver import QuizSolver


class Question:
    def __init__(self, *, quizsolver: 'QuizSolver', quiz_question: dict):
        self._quizsolver = quizsolver
        self._raw_question = RawQuestion(quiz_question=quiz_question, parent_question=self)
        self.type: RawQuestionType = self._raw_question.type
        self.is_solved: bool = False
        self.answers: list[Answer] = []
        # custom data for strategies
        self.data: dict = {}
        self.process_raw_answers()

    def process_raw_answers(self):
        """
        Process raw answers to create Answer objects.
        """
        len_raw_answers = len(self._raw_question.raw_answers)
        if len_raw_answers == 0:
            raise ValueError("A question must have at least one answer.")            
        if len_raw_answers > 65535:
            raise ValueError("A question cannot have more than 65535 answers.")
        if len_raw_answers > 16 and \
            self.type in [RawQuestionType.CHOOSE_ONE_OR_MORE, 
                          RawQuestionType.CHOOSE_ZERO_OR_MORE]:
            raise ValueError("A question with more than 16 answers cannot be of type chooseOneOrMore or chooseZeroOrMore.")
        if self.type == RawQuestionType.CHOOSE_ONE:
            for raw_answer in self._raw_question.raw_answers:
                answer = Answer(raw_answers=[raw_answer])
                self.answers.append(answer)
        elif self.type in [RawQuestionType.CHOOSE_ONE_OR_MORE,
                           RawQuestionType.CHOOSE_ZERO_OR_MORE]:
            s = self._raw_question.raw_answers
            raw_answers_combinations = chain.from_iterable(combinations(s, r) for r in range(len(s)+1))
            start_index = 1 if self.type == RawQuestionType.CHOOSE_ONE_OR_MORE else 0
            for i in range(start_index, len_raw_answers + 1):
                answer = Answer(raw_answers=list(raw_answers_combinations[i]))
                self.answers.append(answer)
        # Mark question as solved if there's only one possible answer
        if len_raw_answers == 1:
            self.is_solved = True
            self.answers[0].is_correct = True

    @property
    def question_text(self) -> str:
        """
        Get the text of the question.
        Returns: Question text as a string.
        """
        return self._raw_question.question_text

    # def duplicate(self) -> 'Question':
    #     """
    #     Create a duplicate of the question with the same properties.
    #     Returns: A new Question object with copied attributes.
    #     """
    #     new_question = Question(quizsolver=self._quizsolver, quiz_question=self._raw_question)
    #     new_question.is_solved = self.is_solved
    #     new_question.answers = [answer.duplicate() for answer in self.answers]
    #     return new_question
    
    @property
    def uid(self) -> str:
        """
        Get the unique identifier of the question.
        Returns: Unique identifier as a string.
        """
        return self._raw_question.uid
    
    def to_dict(self, strategy_name: str = "") -> dict:
        """
        Get dictionary representation of the question.
        Returns: Dictionary with question details and answers.
        """
        answers: list[dict] = []
        for answer in self.answers:
            answers += answer.to_dict()
        return {
            "uid": self.uid,
            "question": self._raw_question._original_value["question"],
            "is_solved": self.is_solved,
            "type": self.type,
            "answers": [answer.to_dict() for answer in self.answers]
        }
    
    def to_response_dict(self, *, strategy_name: str, most_probable_key: str = "most_probable") -> dict:
        """
        Get dictionary representation of the question for response.
        Returns: Dictionary with question details and answers for response.
        """
        answers: list[dict] = []
        for answer in self.answers:
            answers += answer.to_response_list_of_raw_answers(strategy_name=strategy_name,
                                                              most_probable_key=most_probable_key)
        return {
            "uid": self.uid,
            "question": self._raw_question._original_value["question"],
            "is_solved": self.is_solved,
            "type": self.type.value,
            "answers": answers
        }