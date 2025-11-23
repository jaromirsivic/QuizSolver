import random
import json
import matplotlib.pyplot as plt
from dataclasses import dataclass
from package.quizsolver.quizsolversetup import QuizSolverSetup
from .common import epsilon
from .rawquestion import RawQuestion
from .question import Question
from .answer import Answer
from .movingaverage import MovingAverage
from .strategy import Strategy
from .strategyw import StrategyW
from .strategyl import StrategyL
from .strategya import StrategyA
from .strategyb import StrategyB
from consoledraw import Console


@dataclass
class StrategyBSetup:
    measurement_started_at_epoch: int = 0
    measurement_rounds: int = 10
    black_group_cumulative_score: float = 0.0
    black_group_cumulative_weight: float = 0.0
    white_group_cumulative_score: float = 0.0
    white_group_cumulative_weight: float = 0.0
    white_group_percentage: float = 0.1

class QuizSolver:
    def __init__(self, *, quiz_setup: QuizSolverSetup, strategy_in_use: str):
        # Initialize the QuizSolver with the provided QuizSetup.
        self.quiz_setup = quiz_setup
        self.console = Console(hideCursor=False)
        self.latest_result: dict = {}
        # Current epoch of the solving process.
        self.epoch: int = 0
        # Initialize main question dictionary and moving average tracker.
        self.questions: dict[str, Question] = {}
        self.waiting_for_score_feedback: bool = False
        # quiz statistics
        self.avg_quiz_questions_count: MovingAverage
        self.avg_quiz_answers_count: MovingAverage
        self.avg_quiz_probability_baseline: MovingAverage
        # Store the latest quiz as a dictionary of questions.
        self._latest_quiz: list[Question] = []
        self._latest_response: list[Question] = []
        self.strategies: dict[str,Strategy] = {
            "Winner": StrategyW(quizsolver=self, name="Winner"),
            "Looser": StrategyL(quizsolver=self, name="Looser"),
            "Alpha": StrategyA(quizsolver=self, name="Alpha"),
            "NegativeAlpha": StrategyA(quizsolver=self, name="NegativeAlpha", is_negative=True),
            "Beta": StrategyB(quizsolver=self, name="Beta"),
            "NegativeBeta": StrategyB(quizsolver=self, name="NegativeBeta", is_negative=True),
        }
        self._strategy_in_use: Strategy = self.strategies["Beta"]

    # def plot(self):
    #     """
    #     Create a plot composed of 5 subplots.
    #     First subplot: Moving average and median of ma0 and moving average and median of ma1.
    #     Second subplot: Probabilities of all first answers in questions "self.q"
    #     Third subplot: Probabilities of all second answers in questions "self.q"
    #     Fourth subplot: Probabilities of all third answers in questions "self.q"
    #     Fifth subplot: Probabilities of all fourth answers in questions "self.q"
    #     0.01 second pause to update the plot.
    #     """
    #     if not self.figure_initialized:
    #         self.figure, self.axes = plt.subplots(5, 1, figsize=(14, 9))
    #         self.figure_initialized = True
    #     self.axes[0].clear()
    #     self.axes[0].set_title(f'Moving Averages and Medians for Strategy {self._strategy_in_use}. '
    #                            f'Avg0: {self.ma0.moving_average:.4f}, Avg1: {self.ma1.moving_average:.4f}')
    #     self.axes[0].plot(self.ma0.history_of_moving_averages, label='MA0 Moving Average', color='blue')
    #     self.axes[0].plot(self.ma1.history_of_moving_averages, label='MA1 Moving Average', color='cyan')
    #     #self.axes[0].plot(self.ma0.history_of_medians, label='MA0 Median', color='cyan')
    #     self.axes[0].plot(self.ma2.history_of_moving_averages, label='MA2 Moving Average', color='orange')
    #     #self.axes[0].plot(self.ma2.history_of_medians, label='MA2 Median', color='red')
    #     self.axes[0].legend()
    #     x = list(range(len(self.questions[0])))
    #     colors = ['blue' if question.is_white else 'black' for question in self.questions[0].values()]
    #     for i in range(1, 5):
    #         self.axes[i].clear()
    #         #self.axes[i].set_title(f'Probabilities of Answer {i}')
    #         probabilities = []
    #         for question in self.questions[0].values():
    #             if question.most_probable_answer_index == i - 1:
    #                 probabilities.append(question.most_probable_answer.probability)
    #             else:
    #                 probabilities.append(0.0)
    #         self.axes[i].bar(x, probabilities, color=colors, alpha=0.7)
    #     plt.pause(0.01)
    
    # def update_quiz_statistics(self, *, quiz: dict):
    #     """
    #     Update quiz statistics based on the provided quiz data.
    #     Computes average number of questions, answers, and probability baseline.
    #     Probability baseline is a probable score received after randomly picking
    #     an answer for each question.
    #     Args:
    #         quiz (dict): The quiz data containing questions and answers.
    #     """
    #     # Analyze quiz structure
    #     received_raw_questions = quiz.get("questions", [])
    #     num_questions = len(received_raw_questions)
    #     total_answers = 0
    #     total_probability_baseline = 0.0
    #     # Process each question to gather statistics
    #     for received_raw_question in received_raw_questions:
    #         raw_answers = received_raw_question.get("answers", [])
    #         num_answers = len(raw_answers)
    #         total_answers += num_answers
    #         # Assuming uniform probability baseline
    #         if num_answers > 0:
    #             total_probability_baseline += 1.0 / num_answers
    #     avg_answers = total_answers / num_questions if num_questions > 0 else 0
    #     avg_probability_baseline = total_probability_baseline / num_questions if num_questions > 0 else 0.0
    #     # Update moving averages
    #     if not hasattr(self, 'avg_quiz_questions_count'):
    #         self.avg_quiz_questions_count = MovingAverage(initial_value=num_questions, window_size=100)
    #     if not hasattr(self, 'avg_quiz_answers_count'):
    #         self.avg_quiz_answers_count = MovingAverage(initial_value=avg_answers, window_size=100)
    #     if not hasattr(self, 'avg_quiz_probability_baseline'):
    #         self.avg_quiz_probability_baseline = MovingAverage(initial_value=avg_probability_baseline, window_size=100)
    #     self.avg_quiz_questions_count.add_value(num_questions)
    #     self.avg_quiz_answers_count.add_value(avg_answers)
    #     self.avg_quiz_probability_baseline.add_value(avg_probability_baseline)

    def give_answer(self, *, quiz_question: dict) -> dict:
        """
        Solve a single question based on its raw representation.
        Args:
            raw_question (RawQuestion): The raw question to be solved.
        Returns:
            RawQuestion: The solved raw question.
        """
        question = Question(quizsolver=self, quiz_question=quiz_question)
        # Add question to the main questions dictionary if not already present.
        if not question.uid in self.questions:
            # Initialize strategies for the question
            for strategy in self.strategies.values():
                strategy.initialize_question(question=question)
            self.questions[question.uid] = question
        # Retrieve the question from the main dictionary
        question = self.questions[question.uid]
        # add question to the latest quiz
        self._latest_quiz.append(question)
        # Use the current strategy to give an answer.
        result = self._strategy_in_use.give_answer(question=question)
        return result
    
    def _calculate_moving_average_window_size(self) -> int:
        """
        Calculate the moving average window size based on the number of questions.
        Returns:
            int: The calculated window size.
        """
        # If a fixed window size is set in the setup, use it
        if self.quiz_setup.moving_average_window_size is not None:
            return self.quiz_setup.moving_average_window_size
        # Dynamic calculation based on average quiz statistics
        result = 0
        # coefficient = (self.avg_quiz_questions_count.moving_average /
        #                len(self.questions))
        coefficient = (len(self._latest_quiz) / len(self.questions))
        buffer = 0.0
        remaining = 1.0
        while buffer < 0.69:
            delta = coefficient * remaining
            buffer += delta
            remaining -= delta
            result += 1
        return max(result, 1) + 1
    
    @property
    def are_all_questions_solved(self) -> bool:
        """
        Check if all questions have been solved.
        Returns:
            bool: True if all questions are solved, False otherwise.
        """
        for question in self.questions.values():
            if not question.is_solved:
                return False
        return True     
    
    def process_score_feedback(self, *, score: float, max_score: float) -> dict:
        # Update moving average with the new score
        if len(self._latest_quiz) == 0:
            raise ValueError("Not waiting for score feedback. Call solve() method before processing score feedback.")
        if score < 0.0:
            raise ValueError(f"Invalid score: {score}. Score must be non-negative.")
        if max_score <= 0.0:
            raise ValueError(f"Invalid max_score: {max_score}. max_score must be positive.")
        if max_score < score:
            raise ValueError(f"Invalid max_score: {max_score}. max_score must be >= score.")
        # If score is perfect, set all most probable answers to max probability
        self.strategies["Winner"].process_quiz_feedback(score=score, max_score=max_score)
        self.strategies["Looser"].process_quiz_feedback(score=score, max_score=max_score)
        self._strategy_in_use.process_quiz_feedback(score=score, max_score=max_score)
        
        # Reset waiting for score feedback flag
        #self.waiting_for_score_feedback = False
        # Indicate confidence that the quiz solution is 100% correct

        result = {
            "epoch": self.epoch + 1,
            "max_epochs_reached": self.epoch >= self.quiz_setup.max_epochs,
            "strategy_in_use": self._strategy_in_use.name,
            "score": score,
            "max_score": max_score,
            "total_questions": len(self.questions),
            #"quiz_questions_count_moving_average": self.avg_quiz_questions_count.moving_average,
            #"quiz_answers_count_moving_average": self.avg_quiz_answers_count.moving_average,
            #"quiz_probability_baseline_moving_average": self.avg_quiz_probability_baseline.moving_average,
            "all_questions_solved": self.are_all_questions_solved,
            "finished": self.epoch >= self.quiz_setup.max_epochs or self.are_all_questions_solved
        }
        # Update epoch
        self.epoch += 1
        self._latest_quiz = []
        # if False and self.epoch % 2 == 0:
        #     self._strategy_in_use = self.strategies["Alpha"]
        # else:
        #     self._strategy_in_use = self.strategies["NegativeAlpha"]
        # return the result dictionary
        self.latest_result = result
        self.print_statistics()
        return result

    def print_statistics(self):
        """
        Print statistics containing the state of all questions.
        """
        result = "QuizSolver Statistics:\n"
        result +=f"  Epoch: {self.latest_result["epoch"]}\n"
        result += f"  Total Questions: {self.latest_result["total_questions"]}\n"
        result += f"  Latest Score %: {(self.latest_result["score"]/self.latest_result["max_score"]) * 100:.3f}% " \
                  f"({self.latest_result["score"]:.5f} / {self.latest_result["max_score"]:.5f})\n"
        result += f"  All Questions Solved: {self.latest_result["all_questions_solved"]}\n\n"
        result += self.strategies["Winner"].print_statistics()+"\n"
        result += self.strategies["Looser"].print_statistics()+"\n"
        result += self.strategies["Alpha"].print_statistics()+"\n"
        result += self.strategies["NegativeAlpha"].print_statistics()+"\n"
        result += self.strategies["Beta"].print_statistics()+"\n"
        result += self.strategies["NegativeBeta"].print_statistics()+"\n"
        try:
            self.console.clear()
            self.console.print(result)
            self.console.update()
        except Exception as e:
            print(result)