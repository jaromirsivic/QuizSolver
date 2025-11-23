import random
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .answer import Answer
    from .question import Question
    from .quizsolver import QuizSolver

class Strategy:
    def __init__(self, *, quizsolver: 'QuizSolver', name: str = "BaseStrategy"):
        self._quizsolver = quizsolver
        self.name = name
        self.epochs_used = 0
        self.enabled = True

    def initialize_question(self, *, question: 'Question'):
        """
        Initialize the strategy before starting the quiz solving process.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def give_answer(self, *, question: 'Question') -> dict:
        """
        Process a question when it is presented in the quiz.
        Args:
            question (Question): The question to process.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def process_quiz_feedback(self, *, score: float, max_score: float):
        """
        Process feedback after a quiz has been submitted and scored.
        Args:
            score (float): The score received for the submitted quiz.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def plot(self):
        """
        Plot any relevant data for the strategy.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def print_statistics(self) -> str:
        """
        Print statistics related to the strategy's performance.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def get_progress(self) -> float:
        """
        Get the current progress of the strategy.
        Returns:
            float: A value between 0.0 and 1.0 indicating progress.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")