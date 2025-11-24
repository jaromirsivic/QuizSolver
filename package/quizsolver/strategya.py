import random
from matplotlib import pyplot as plt
from .common import epsilon, minmax, inverse_square_likelyhood
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
        # Variables for charts
        self.figure_initialized: bool = False
        self.figure = None
        self.axes: list = []
        self.axes_data: list = []

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
        # Update window size at powers of two epochs
        if (epoch & (epoch - 1)) == 0 and self._ma is not None:
            # Determine window size
            if self._quizsolver.setup.moving_average_window_size_override is not None:
                window_size = self._quizsolver.setup.moving_average_window_size_override
            else:
                window_size = self._quizsolver._calculate_moving_average_window_size() + 5
            # Update moving average window size if different
            if self._ma.window_size != window_size:
                self._ma.set_window_size(window_size)

    # def get_questions_to_train(self) -> list['Question']:
    #     """
    #     Determine which questions from the latest quiz should be included in the training batch.
    #     Returns:
    #         list of Question: The list of questions to include in the training batch.
    #     """
    #     # If there are no questions, return empty list
    #     len_all_questions = len(self._quizsolver.questions)
    #     if len_all_questions == 0:
    #         return []
    #     # Get questions from latest quiz
    #     questions_in_latest_quiz = self._quizsolver._latest_quiz
    #     len_questions_in_latest_quiz = len(questions_in_latest_quiz)
    #     # Find min and max counter among most probable answers in latest quiz
    #     min_counter, _, max_counter, _ = minmax(
    #         questions_in_latest_quiz,
    #         key=lambda q: q.data[self.name]["most_probable_answer"].data[self.name]["counter"]
    #     )
    #     # Compute minimum likelyhood based on proportion of questions in latest quiz compared to all questions
    #     #min_likelyhood = min(max(0.3, 1 - (len_questions_in_latest_quiz / len_all_questions)), 1.0)
    #     #min_likelyhood = min_likelyhood ** 2
    #     progress = self.get_progress()
    #     min_likelyhood = min(max(0.3, 1 - progress), 1.0)
    #     #min_likelyhood = min_likelyhood ** 2 
    #     min_likelyhood = 1.0
    #     # Prepare result list
    #     result = []
    #     # Assign questions to training batch based on counter
    #     for question in questions_in_latest_quiz:
    #         counter = question.data[self.name]["most_probable_answer"].data[self.name]["counter"]
    #         random_value = random.uniform(0, 1)
    #         likelyhood_in_training_batch = inverse_square_likelyhood(
    #             min=min_counter,
    #             max=max_counter,
    #             min_likelyhood=min_likelyhood,
    #             max_likelyhood=1.0,
    #             value=counter
    #         )
    #         # Determine if question is included in the training batch
    #         in_training_batch = random_value <= likelyhood_in_training_batch + epsilon
    #         if in_training_batch:
    #             result.append(question)
    #     return result
    
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
        # Initialize and update moving average
        self._initialize_moving_average()
        if self._ma is None:
            raise ValueError("Moving average not initialized.")
        self._update_moving_average_window_size()
        # Update moving average with current factor
        self._ma.add_value(factor)
        # shuffle sorted latest quiz questions
        questions_to_train = self._quizsolver._latest_quiz
        #questions_to_train = self.get_questions_to_train()
        # train answer probabilities
        for question in questions_to_train:
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

    def get_progress(self) -> float:
        """
        Get the current progress of the strategy based on the moving average.
        Returns:
            float: The current progress as a float between 0.0 and 1.0.
        """
        if self._ma is None:
            return 0.0
        if not self.is_negative:
            return self._ma.moving_average
        else:
            return 1.0 - self._ma.moving_average
    
    def plot(self):
        """
        Create a plot composed of 5 subplots.
        First subplot: Moving average and median of ma0 and moving average and median of ma1.
        Second subplot: Probabilities of all first answers in questions "self.q"
        Third subplot: Probabilities of all second answers in questions "self.q"
        Fourth subplot: Probabilities of all third answers in questions "self.q"
        Fifth subplot: Probabilities of all fourth answers in questions "self.q"
        0.01 second pause to update the plot.
        """
        rows = 5
        cols = 1
        answers_per_row = 400
        # Calculate maximum answers to plot
        max_answers = rows * answers_per_row
        # Initialize figure and axes if not already done
        if not self.figure_initialized:
            self.figure, self.axes = plt.subplots(rows, cols, figsize=(13, 5.5))
            self.figure_initialized = True
            # initialize axes data
            for row in range(rows):
                self.axes_data.append([])
        # Check if moving averages are initialized
        if self._ma is None:
            return
        # Clear and update first subplot
        self.axes[0].clear()
        self.axes[0].set_title(f'Strategy {self.name}. '
                               f'Avg0: {self._ma.moving_average:.4f}')
        self.axes[0].plot(self._ma.history_of_moving_averages, label='MA Moving Average', color='blue')
        self.axes[0].legend()
        
        # Clear and update other subplots
        for i in range(1, 5):
            self.axes[i].clear()
        # draw answers
        colors = []
        answers = []
        answers_count = 0
        questions = list(self._quizsolver.questions.values())
        for question in questions:
            # If the limit of answers to plot is reached, break
            if answers_count >= max_answers:
                break
            for answer in question.answers:
                # If the limit of answers to plot is reached, break
                if answers_count >= max_answers:
                    break
                if answer.data[self.name]["counter"] > 0:
                    colors.append('black')
                    answers.append(answer.data[self.name]["counter"])
                else:
                    colors.append('lightgray')
                    answers.append(0.5)
            # increment answers count
            answers_count += len(question.answers) + 4
            colors.append('lightgray')
            colors.append('lightgray')
            colors.append('lightgray')
            colors.append('lightgray')
            answers.append(0)
            answers.append(0)
            answers.append(0)
            answers.append(0)

        if len(answers) < max_answers:
            # pad answers and colors to max_answers
            answers += [0] * (max_answers - len(answers))
            colors += ['black'] * (max_answers - len(colors))

        for i in range(1, 5):
            # get data for this subplot
            start_index = (i - 1) * answers_per_row
            end_index = start_index + answers_per_row
            data = answers[start_index:end_index]
            color_data = colors[start_index:end_index]
            self.axes[i].xaxis.set_visible(False)
            self.axes[i].bar(range(len(data)), data, color=color_data, alpha=0.7)

        plt.pause(0.01)
    
    def print_statistics(self) -> str:
        """
        Print statistics related to the strategy's performance.
        """
        # return statistics
        #factor = self.latest_score / self.latest_max_score if self.latest_max_score > 0 else 0.0
        window_size = self._ma.window_size if self._ma else 0
        moving_average = self._ma.moving_average if self._ma else 0.0
        result = f'Strategy {self.name} ({"Enabled" if self.enabled else "Disabled"}):\n'
        result += f'  Epochs used: {self.epochs_used}\n'
        result += f'  Moving Average: {moving_average * 100:,.3f}% (Window Size={window_size})\n'
        # draw progress bar
        bar_length = 50
        bar_used = int(self.get_progress() * bar_length)
        result += f"[" + "#" * bar_used + "-" * (bar_length - bar_used) + "]\n"
        return result