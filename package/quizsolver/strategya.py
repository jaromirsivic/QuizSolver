import random
from .common import epsilon
from .strategy import Strategy
from .movingaverage import MovingAverage
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .answer import Answer
    from .question import Question
    from .quizsolver import QuizSolver

class StrategyA(Strategy):
    def __init__(self, *, quizsolver: 'QuizSolver', name: str = "A", is_negative: bool = False):
        super().__init__(quizsolver=quizsolver, name=name)
        self._ma: MovingAverage | None = None
        self.is_negative = is_negative
        self.latest_score: float = 0.0
        self.latest_max_score: float = 1.0

    def initialize_question(self, *, question: 'Question'):
        """
        Initialize the strategy before starting the quiz solving process.
        """
        # Initialize data for each answer
        for answer in question.answers:
            answer.data[self.name] = {
                "most_probable": False,
                "counter": 0
            }
        # Select a random most probable answer
        random_index = random.randint(0, len(question.answers) - 1)
        question.answers[random_index].data[self.name] = {
            "most_probable": True,
            "counter": 1
        }
        # Store most probable answer in question data
        question.data[self.name] = {
            "most_probable_answer": question.answers[random_index]
        }

    def give_answer(self, *, question: 'Question') -> dict:
        """
        Process a question when it is presented in the quiz.
        Args:
            question (Question): The question to process.
        """
        return question.to_response_dict(strategy_name=self.name)
    
    def _change_most_probable_answer(self, question: 'Question'):
        """
        Change the most probable answer for a question to a different random answer.
        Args:
            question (Question): The question to process.
        """
        # Get list of possible answers to select from
        possible_answers = []
        for answer in question.answers:
            #if answer.is_correct is None and answer != most_probable_answer:
            if answer.is_correct is None:
                possible_answers.append(answer)
        # this should never happen        
        if len(possible_answers) < 2:
            raise ValueError("No possible answers to select from in strategy Alpha / Negative Alpha. "
                             "This should not happen.")
        # Select a new most probable answer randomly from possible answers
        # and initialize its data
        new_most_probable_answer = random.choice(possible_answers)
        new_most_probable_answer.data[self.name]["most_probable"] = True
        new_most_probable_answer.data[self.name]["counter"] = 1
        # Update question data
        question.data[self.name]["most_probable_answer"] = new_most_probable_answer
        # Reset data for other answers
        for answer in question.answers:
            if answer != new_most_probable_answer:
                answer.data[self.name]["most_probable"] = False
                answer.data[self.name]["counter"] = 0

    def _initialize_moving_average(self):
        """
        Initialize the moving average for tracking score changes.
        """
        # if moving average is not initialized
        if self._ma is None:
            # compute initial average probability
            probability = []
            for question in self._quizsolver._latest_quiz:
                probability.append(1 / len(question.answers))
            average_probability = sum(probability) / len(probability)
            # initialize moving average
            self._ma = MovingAverage(initial_value=average_probability)

    def _update_moving_average_window_size(self):
        """
        Update the moving average window size based on the current epoch.
        """
        epoch = self._quizsolver.epoch
        if (epoch & (epoch - 1)) == 0 and self._ma is not None:
            window_size = self._quizsolver._calculate_moving_average_window_size() + 5
            if self._ma.window_size != window_size:
                self._ma.set_window_size(window_size)

    # def compute_min_counter_across_all_questions(self) -> int:
    #     """
    #     Compute the moving average of the most probable answer probabilities among all questions.
    #     Returns:
    #         float: The computed moving average.
    #     """
    #     min_counter = 65535
    #     for question in self._quizsolver.questions.values():
    #         most_probable_answer: Answer = question.data[self.name]["most_probable_answer"]
    #         counter = most_probable_answer.data[self.name]["counter"]
    #         if counter < min_counter:
    #             min_counter = counter
    #     if min_counter < 1:
    #         raise ValueError("Minimum counter is less than 1, which should not happen.")
    #     return min_counter
    
    # def normalize_counters_across_all_questions(self):
    #     """
    #     Normalize the counters of the most probable answers across all questions.
    #     """
    #     min_counter = self.compute_min_counter_across_all_questions()
    #     if min_counter <= 1:
    #         return
    #     delta = min_counter - 1
    #     for question in self._quizsolver.questions.values():
    #         most_probable_answer: Answer = question.data[self.name]["most_probable_answer"]
    #         most_probable_answer.data[self.name]["counter"] -= delta

    def _shuffle_sort(self, questions):
        """
        Shuffle and sort questions based on most probable answer probability.
        Args:
            questions (list of Question): The list of questions to process.
        Returns:
            list of Question: The shuffled and sorted list of questions.
        """
        random.shuffle(questions)
        sorted_questions = sorted(
            questions,
            key=lambda q: q.data[self.name]["most_probable_answer"].data[self.name]["counter"]
        )
        return sorted_questions

    def compute_k_split(self) -> int:
        total_questions = len(self._quizsolver.questions)
        quiz_questions = len(self._quizsolver._latest_quiz)
        quiz_multiplier = quiz_questions / total_questions
        rand_gaussian = min(1, max(-1, random.gauss(mu=0.0, sigma=0.15)))
        quiz_multiplier += rand_gaussian * quiz_multiplier
        k = min(max(1, int((1 - quiz_multiplier) * quiz_questions)) + random.randint(-2, 2), quiz_questions)
        return k

    def process_quiz_feedback(self, *, score: float, max_score: float):
        """
        Process feedback after a quiz has been submitted and scored.
        Args:
            score (float): The score received for the submitted quiz.
        """
        self.epochs_used += 1
        # compute score factor
        factor = score / max_score
        # store latest score and max score
        self.latest_score = score
        self.latest_max_score = max_score
        # normalize counters across all questions
        #self.normalize_counters_across_all_questions()
        # Initialize and update moving average
        self._initialize_moving_average()
        if self._ma is None:
            raise ValueError("Moving average not initialized.")
        self._update_moving_average_window_size()
        # Update moving average with current factor
        self._ma.add_value(factor)
        # shuffle sorted latest quiz questions
        sorted_latest_quiz = self._quizsolver._latest_quiz
        # sorted_latest_quiz = self._shuffle_sort(self._quizsolver._latest_quiz)
        # k = self.compute_k_split()
        # if random.random() < 1.0:
        #     sorted_latest_quiz = sorted_latest_quiz[:k]
        # train answer probabilities
        for question in sorted_latest_quiz:
            # If question is already solved then continue
            if question.is_solved:
                continue
            # select most probable answer
            most_probable_answer: Answer = question.data[self.name]["most_probable_answer"]
            # If the most probable answer is marked as incorrect, change it
            if most_probable_answer.is_correct == False:
                self._change_most_probable_answer(question)
            # Update counter based on score factor and moving average
            elif (factor - epsilon > self._ma.moving_average and self.is_negative == False) or \
                 (factor + epsilon < self._ma.moving_average and self.is_negative == True):
                # Increase counter for most probable answer
                most_probable_answer.data[self.name]["counter"] += 1
            else:
                # Decrease counter for most probable answer
                most_probable_answer.data[self.name]["counter"] -= 1
                # Change most probable answer if counter is zero or negative
                if most_probable_answer.data[self.name]["counter"] <= epsilon:
                    self._change_most_probable_answer(question)

    
    def plot(self):
        """
        Plot any relevant data for the strategy.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    # def print_statistics(self) -> str:
    #     """
    #     Print statistics related to the strategy's performance.
    #     """
    #     # return statistics
    #     factor = self.latest_score / self.latest_max_score if self.latest_max_score > 0 else 0.0
    #     window_size = self._ma.window_size if self._ma else 0
    #     moving_average = self._ma.moving_average if self._ma else 0.0
    #     result = f"Strategy {self.name}:\n"
    #     result += f"  Enabled: {self.enabled}\n"
    #     result += f"  Epochs used: {self.epochs_used}\n"
    #     result += f"  MA Window Size: {window_size}\n"
    #     result += f"  Moving Average: {moving_average * 100:,.3f}%\n"
    #     result += f"  Latest Score% : {(self.latest_score/self.latest_max_score) * 100:.3f}% " \
    #               f"({self.latest_score:.5f} / {self.latest_max_score:.5f})\n"
    #     # draw progress bar
    #     bar_length = 50
    #     factor2 = factor
    #     bar_used = int(factor2 * bar_length)
    #     result += f"[" + "#" * bar_used + "-" * (bar_length - bar_used) + "]\n"
    #     return result
    
    def print_statistics(self) -> str:
        """
        Print statistics related to the strategy's performance.
        """
        # return statistics
        factor = self.latest_score / self.latest_max_score if self.latest_max_score > 0 else 0.0
        window_size = self._ma.window_size if self._ma else 0
        moving_average = self._ma.moving_average if self._ma else 0.0
        result = f'Strategy {self.name} ({"Enabled" if self.enabled else "Disabled"}):\n'
        result += f'  Epochs used: {self.epochs_used}\n'
        result += f'  Moving Average: {moving_average * 100:,.3f}% (Window Size={window_size})\n'
        # draw progress bar
        bar_length = 50
        factor2 = factor
        bar_used = int(factor2 * bar_length)
        result += f"[" + "#" * bar_used + "-" * (bar_length - bar_used) + "]\n"
        return result