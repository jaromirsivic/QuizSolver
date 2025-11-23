import random
from .strategy import Strategy
from .common import epsilon
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .answer import Answer
    from .question import Question
    from .quizsolver import QuizSolver

class StrategyW(Strategy):
    def __init__(self, *, quizsolver: 'QuizSolver', name: str = "W"):
        super().__init__(quizsolver=quizsolver, name=name)
        # How many times was this strategy used to close questions
        self.win_strike_count = 0
        # How many questions were solved by this strategy
        self.questions_solved = 0
        # How many answers were closed by this strategy
        self.answers_closed = 0

    def initialize_question(self, *, question: 'Question'):
        """
        Initialize the strategy before starting the quiz solving process.
        """
        # Initialize data for each answer
        for answer in question.answers:
            answer.data[self.name] = {"most_probable": False}
        random_index = random.randint(0, len(question.answers) - 1)
        question.answers[random_index].data[self.name]["most_probable"] = True
        # Store most probable answer in question data
        question.data[self.name] = {"most_probable_answer": question.answers[random_index]}

    def give_answer(self, *, question: 'Question') -> dict:
        """
        Process a question when it is presented in the quiz.
        Args:
            question (Question): The question to process.
        """
        raise NotImplementedError("This method is not applicable for this strategy.")

    def process_quiz_feedback(self, *, score: float, max_score: float):
        """
        Process feedback after a quiz has been submitted and scored.
        Args:
            score (float): The score received for the submitted quiz.
        """
        self.epochs_used += 1
        # if score is not perfect, do nothing
        if score < max_score - epsilon:
            return
        # if score is perfect, increment win strike count
        self.win_strike_count += 1
        # If the score is perfect, mark the most probable answers as correct
        for question in self._quizsolver._latest_quiz:
            # If question is already solved then continue
            if question.is_solved:
                continue
            # Mark the question as solved
            question.is_solved = True
            self.questions_solved += 1
            # Mark the most probable answer as correct
            for answer in question.answers:
                answer.is_correct = False
                self.answers_closed += 1
            most_probable_answer: Answer = question.data[self._quizsolver._strategy_in_use.name]["most_probable_answer"]
            most_probable_answer.is_correct = True
            # Mark the question of this strategy as solved
            question.data[self.name]["most_probable_answer"] = most_probable_answer
    
    def plot(self):
        """
        Plot any relevant data for the strategy.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def print_statistics(self) -> str:
        """
        Print statistics related to the strategy's performance.
        """
        result = f'Strategy {self.name} ({"Enabled" if self.enabled else "Disabled"}):\n'
        result += f'  Epochs used: {self.epochs_used}\n'
        result += f'  Triggered / Questions Solved / Answ. Closed: ' \
                  f'{self.win_strike_count} / {self.questions_solved} / {self.answers_closed}\n'
        return result