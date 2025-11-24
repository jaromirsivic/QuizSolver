import datetime
import random
import json
import matplotlib.pyplot as plt
from dataclasses import dataclass
from .common import epsilon
from .quizsolversetup import QuizSolverSetup
from .quizsolverstatistics import QuizSolverStatistics
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


class QuizSolver:
    def __init__(self, *, setup: QuizSolverSetup, strategy_in_use: str):
        # Initialize the QuizSolver with the provided QuizSetup.
        self.setup = setup
        self.statistics = QuizSolverStatistics()
        self.console = Console(hideCursor=False)
        self.latest_result: dict = {}
        # Current epoch of the solving process.
        self.epoch: int = 0
        # Initialize main question dictionary and moving average tracker.
        self.questions: dict[str, Question] = {}
        self.waiting_for_score_feedback: bool = False
        # Timestamp of the latest quiz processed.
        self.console_redrawn_at: datetime.datetime = datetime.datetime.min
        self.plots_rendered_at: datetime.datetime = datetime.datetime.min
        # self.avg_quiz_questions_count: MovingAverage
        # self.avg_quiz_answers_count: MovingAverage
        # self.avg_quiz_probability_baseline: MovingAverage
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
        self.determine_strategy()
    
    def update_quiz_statistics(self, *, score: float):
        """
        Update quiz statistics based on the latest quiz results.
        Args:
            score (float): The score obtained in the latest quiz.
        """
        # Analyze quiz structure
        statistics = self.statistics
        # Calculate total number of questions and answers
        questions_total = len(self.questions)
        if questions_total != statistics["questions_total"]:
            answers_total = sum(len(q.answers) for q in self.questions.values())
        else:
            answers_total = statistics["answers_total"]
        len_questions_in_latest_quiz = len(self._latest_quiz)
        len_answers_in_latest_quiz = sum(len(q.answers) for q in self._latest_quiz)
        # Update finished_at if needed
        if self.epoch >= self.setup.max_epochs or self.are_all_questions_solved:
            statistics["finished_at"] = datetime.datetime.now()
        # Update epoch
        statistics["epochs"] = self.epoch + 1
        # Update min score
        if statistics["min_score"] is None or score < statistics["min_score"]:
            statistics["min_score"] = score
            statistics["min_score_epoch"] = self.epoch
        # Update max score
        if statistics["max_score"] is None or score > statistics["max_score"]:        
            statistics["max_score"] = score
            statistics["max_score_epoch"] = self.epoch
        # Update questions and answers counts
        statistics["questions_total"] = questions_total
        statistics["answers_total"] = answers_total
        statistics["sum_of_all_questions_of_all_quizzes"] += len_questions_in_latest_quiz
        statistics["sum_of_all_answers_of_all_quizzes"] += len_answers_in_latest_quiz
        statistics["questions_per_quiz_on_average"] = statistics["sum_of_all_questions_of_all_quizzes"] / (self.epoch + 1)
        statistics["answers_per_quiz_on_average"] = statistics["sum_of_all_answers_of_all_quizzes"] / (self.epoch + 1)      

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
        if self.setup.moving_average_window_size_override is not None:
            return self.setup.moving_average_window_size_override
        # Dynamic calculation based on quiz statistics
        result = 0
        coefficient = (len(self._latest_quiz) / len(self.questions))
        buffer = 0.0
        remaining = 1.0
        # How many iterations are needed to cover at least 69% of the questions
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

    def determine_strategy(self):
        """
        Determine the strategy to use for the next quiz.
        """
        # If a preferred strategy is set in the setup, use it
        if self.setup.preferred_strategy is not None:
            strategy_name = self.setup.preferred_strategy
            strategy_name_lower = strategy_name.lower()
            if strategy_name_lower != "alpha" and strategy_name_lower != "negativealpha" and \
               strategy_name_lower != "beta" and strategy_name_lower != "negativebeta":
                raise ValueError(f"Invalid preferred strategy: {self.setup.preferred_strategy}. "
                                 f"Must be one of: Alpha, NegativeAlpha, Beta, NegativeBeta.")
            # Set the strategy in use
            self._strategy_in_use = self.strategies[strategy_name]
            return
        # if all questions are solved, use the alpha strategy to solve the quiz
        if self.are_all_questions_solved:
            # If all questions are solved, use the Winner strategy
            self._strategy_in_use = self.strategies["Alpha"]
            return
        # Get the number of questions
        len_questions = len(self.questions)
        len_questions_in_latest_quiz = len(self._latest_quiz)
        if len_questions == 0:
                # If no questions yet, use Alpha strategy
                self._strategy_in_use = self.strategies["Alpha"]
                return
        quiz_questions_ratio = len_questions_in_latest_quiz / len_questions
        # Otherwise, choose the strategy based on performance
        # If user wants to obtain 100% score choose negative strategies first
        if self.setup.targeted_score >= 1:
            if quiz_questions_ratio > 0.9:
                self._strategy_in_use = self.strategies["NegativeBeta"]
            else:
                self._strategy_in_use = self.strategies["NegativeAlpha"]
        else:
            if quiz_questions_ratio > 0.9:
                self._strategy_in_use = self.strategies["Beta"]
            else:
                self._strategy_in_use = self.strategies["Alpha"]
            
        
    
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
            "strategy_in_use": self._strategy_in_use.name,
            "score": score,
            "max_epochs_reached": self.epoch >= self.setup.max_epochs,
            "targeted_score_reached": score >= self.setup.targeted_score,
            "all_questions_solved": self.are_all_questions_solved,
            "finished": self.epoch >= self.setup.max_epochs or self.are_all_questions_solved or
                        score >= self.setup.targeted_score
        }
        # return the result dictionary
        self.latest_result = result
        # Update quiz statistics
        self.update_quiz_statistics(score=score)
        # Determine the strategy to use for the next quiz
        self.determine_strategy()
        # Handle console redraw and plot rendering based on intervals
        now = datetime.datetime.now()
        if now - self.console_redrawn_at > datetime.timedelta(seconds=self.setup["redraw_console_interval"]) and self.setup["redraw_console_interval"] >= 0:
            self.print_statistics()
            self.console_redrawn_at = now
        if now - self.plots_rendered_at > datetime.timedelta(seconds=self.setup["render_plots_interval"]) and self.setup["render_plots_interval"] >= 0:
            if self.epoch > 1:
                self._strategy_in_use.plot()
            self.plots_rendered_at = now
        # Update epoch
        self.epoch += 1
        self._latest_quiz = []
        return result

    def print_statistics(self):
        """
        Print statistics containing the state of all questions.
        """
        result = "QuizSolver Statistics:\n"
        result +=f"  Epoch: {self.latest_result["epoch"]}\n"
        result += f"  Total Questions / Answers: {self.statistics["questions_total"]} / {self.statistics["answers_total"]}\n"
        result += f"  Avg Questions / Answers per Quiz: {self.statistics["questions_per_quiz_on_average"]:.3f} / " \
                  f"{self.statistics["answers_per_quiz_on_average"]:.3f}\n"
        result += f"  Latest Score %: {(self.latest_result["score"]) * 100:.3f}% " \
                  f"({self.latest_result["score"]:.5f})\n"
        result += f"  Score Min/Max: {self.statistics["min_score"]:.5f} (Epoch {self.statistics["min_score_epoch"]}) / " \
                  f"{self.statistics["max_score"]:.5f} (Epoch {self.statistics["max_score_epoch"]})\n"
        result += f"  All Questions Solved: {self.latest_result["all_questions_solved"]}\n\n"
        result += self.strategies["Winner"].print_statistics()+"\n"
        result += self.strategies["Looser"].print_statistics()+"\n"
        # result += self.strategies["Alpha"].print_statistics()+"\n"
        # result += self.strategies["NegativeAlpha"].print_statistics()+"\n"
        # result += self.strategies["Beta"].print_statistics()+"\n"
        # result += self.strategies["NegativeBeta"].print_statistics()+"\n"
        result += self._strategy_in_use.print_statistics()+"\n"
        try:
            self.console.clear()
            self.console.print(result)
            self.console.update()
        except Exception as e:
            print(result)