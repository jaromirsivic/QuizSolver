import random
from .common import epsilon, inverse_square_likelyhood, minmax
from .strategy import Strategy
from .movingaverage import MovingAverage
import matplotlib.pyplot as plt
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .answer import Answer
    from .question import Question
    from .quizsolver import QuizSolver

class StrategyB(Strategy):
    def __init__(self, *, quizsolver: 'QuizSolver', name: str = "B", is_negative: bool = False):
        super().__init__(quizsolver=quizsolver, name=name)
        self.finished_measurements: int = 0
        self._ma0: MovingAverage | None = None
        self._ma1: MovingAverage | None = None
        self._ma2: MovingAverage | None = None
        # self.training_group: list['Question'] = []
        self.training_batch: list['Question'] = []
        self.training_minibatch: list['Question'] = []
        self.is_negative = is_negative
        self.latest_score: float = 0.0
        self.latest_max_score: float = 1.0
        self.window_size_delta: int = 0
        # Variables for charts
        self.figure_initialized: bool = False
        self.figure = None
        self.axes: list = []
        self.axes_data: list = []

    def pick_training_batch(self):
        """
        Pick a training batch of questions for the current quiz.
        """
        self.training_batch = []
        # Get all questions from the quiz solver
        all_questions = list(self._quizsolver.questions.values())
        len_all_questions = len(all_questions)
        # If there are no questions, set training group to empty and return
        if len_all_questions == 0:
            return
        # Get min and max counter1 values across all questions
        min_counter1, _, max_counter1, _ = minmax(
            all_questions,
            key=lambda q: q.data[self.name]["most_probable_answer1"].data[self.name]["counter1"]
        )
        # Compute difference between min and max counter1
        min_max_counter_diff = max_counter1 - min_counter1
        # Determine minimum likelyhood based on counter difference
        if min_max_counter_diff < 2.5:
            min_likelyhood = 0.5
        elif min_max_counter_diff < 4.5:
            min_likelyhood = 0.3
        elif min_max_counter_diff < 8.5:
            min_likelyhood = 0.2
        else:
            min_likelyhood = 0.1
        # Assign questions to training batch based on counter1
        for question in all_questions:
            counter1 = question.data[self.name]["most_probable_answer1"].data[self.name]["counter1"]
            random_value = random.uniform(0, 1)
            likelyhood_in_training_batch = inverse_square_likelyhood(
                min=min_counter1,
                max=max_counter1,
                min_likelyhood=min_likelyhood,
                max_likelyhood=1.0,
                value=counter1
            )
            in_training_batch = random_value <= likelyhood_in_training_batch + epsilon
            #question.data[self.name]["in_training_batch"] = in_training_batch
            # Add question to result if it is in training batch
            if in_training_batch:
                self.training_batch.append(question)

    def pick_training_minibatch(self, *, how_many_to_pick: int | None = None):
        # Reset training batch if empty
        if len(self.training_batch) == 0:
            self.pick_training_batch()
        # Pick random questions from training batch and store them in training minibatch
        self.training_minibatch = random.sample(
            self.training_batch,
            k=min(how_many_to_pick if how_many_to_pick is not None else 1,
                  len(self.training_batch))
        )
        # Remove selected questions from training batch
        questions_to_remove = []
        for question in self.training_batch:
            if question in self.training_minibatch:
                questions_to_remove.append(question)
        for question in questions_to_remove:
            self.training_batch.remove(question)
        


    # def pick_training_group(self):
    #     """
    #     Pick a training group of questions for the current quiz.
    #     """
    #     # Get all questions from the quiz solver
    #     all_questions = list(self._quizsolver.questions.values())
    #     len_all_questions = len(all_questions)
    #     # If there are no questions, set training group to empty and return
    #     if len_all_questions == 0:
    #         self.training_group = []
    #         return
    #     if self._ma0 is None:
    #         raise ValueError("Moving average not initialized.")
        
    #     #k = max(1, int(len_all_questions * 0.1))
    #     if random.random() < 1.0:
    #         all_questions_sorted = sorted(
    #             all_questions,
    #             key=lambda q: q.data[self.name]["selected_for_measurement_counter"]
    #         )
    #         first_question = all_questions_sorted[0]
    #         last_question = all_questions_sorted[-1]
    #         k = len_all_questions
    #         if first_question.data[self.name]["selected_for_measurement_counter"] != \
    #         last_question.data[self.name]["selected_for_measurement_counter"]:
    #             for i in range(len_all_questions - 1, -1, -1):
    #                 question = all_questions_sorted[i]
    #                 if question.data[self.name]["selected_for_measurement_counter"] != \
    #                 last_question.data[self.name]["selected_for_measurement_counter"]:
    #                     k = i + 1
    #                     break
    #         all_questions_sorted = all_questions_sorted[:k]
    #         len_all_questions_sorted = len(all_questions_sorted)
    #         # Pick questions randomly for the training group
    #         questions_to_pick = min(max(1, int(0.0001 * len_all_questions)), len_all_questions_sorted)
    #         questions_to_pick = min(max(1, int((1 - self._ma0.moving_average) * questions_to_pick)), len_all_questions_sorted)
    #         self.training_group = random.sample(all_questions_sorted[:k], questions_to_pick)
    #     else:
    #         all_questions = [_ for _ in all_questions if not _.is_solved]
    #         random.shuffle(all_questions)
    #         all_questions_sorted = sorted(
    #             all_questions,
    #             key=lambda q: q.data[self.name]["most_probable_answer1"].data[self.name]["counter1"]
    #         )
    #         len_all_questions_sorted = len(all_questions_sorted)
    #         questions_to_pick = min(max(1, int(0.1 * len_all_questions)), len_all_questions_sorted)
    #         # all_questions_sorted = sorted(
    #         #     all_questions_sorted,
    #         #     key=lambda q: q.data[self.name]["most_probable_answer1"].data[self.name]["counter1"]
    #         # )
    #         self.training_group = all_questions_sorted[:questions_to_pick]

    #         # random.shuffle(all_questions_sorted)
    #         # all_questions_sorted = sorted(
    #         #     all_questions_sorted,
    #         #     key=lambda q: q.data[self.name]["most_probable_answer1"].data[self.name]["counter1"]
    #         # )
    #         # self.training_group = all_questions_sorted[:questions_to_pick]
    #     for question in self.training_group:
    #         question.data[self.name]["selected_for_measurement_counter"] += 1

    def initialize_question(self, *, question: 'Question'):
        """
        Initialize the strategy before starting the quiz solving process.
        """
        # Initialize data for each answer
        for answer in question.answers:
            answer.data[self.name] = {
                "most_probable": False,
                "most_probable1": False,
                "most_probable2": False,
                "counter1": 0,
                "counter2": 0
            }
        # Select a random most probable answer 1
        random_index1 = random.randint(0, len(question.answers) - 1)
        question.answers[random_index1].data[self.name]["most_probable"] = True
        question.answers[random_index1].data[self.name]["most_probable1"] = True
        question.answers[random_index1].data[self.name]["counter1"] = 1
        # Select a random most probable answer 2
        random_index2 = random.randint(0, len(question.answers) - 1)
        question.answers[random_index2].data[self.name]["most_probable2"] = True
        question.answers[random_index2].data[self.name]["counter2"] = 1
        # Store most probable answer in question data
        question.data[self.name] = {
            "selected_for_measurement_counter": 0,
            "most_probable_answer": question.answers[random_index1],
            "most_probable_answer1": question.answers[random_index1],
            "most_probable_answer2": question.answers[random_index2]
        }

    def give_answer(self, *, question: 'Question') -> dict:
        """
        Process a question when it is presented in the quiz.
        Args:
            question (Question): The question to process.
        """
        if self.epochs_used % 2 == 1 and question in self.training_minibatch:
            for answer in question.answers:
                answer.data[self.name]["most_probable"] = answer.data[self.name]["most_probable2"]
            question.data[self.name]["most_probable_answer"] = question.data[self.name]["most_probable_answer2"]
            return question.to_response_dict(strategy_name=self.name)
            # return question.to_response_dict(strategy_name=self.name,
            #                                  most_probable_key="most_probable2")
        else:
            for answer in question.answers:
                answer.data[self.name]["most_probable"] = answer.data[self.name]["most_probable1"]
            question.data[self.name]["most_probable_answer"] = question.data[self.name]["most_probable_answer1"]
            return question.to_response_dict(strategy_name=self.name)
            # return question.to_response_dict(strategy_name=self.name,
            #                                  most_probable_key="most_probable1")
    
    def _change_most_probable_answer1(self, question: 'Question'):
        """
        Change the most probable answer for a question.
        Answer1 always converts to Answer2.
        Args:
            question (Question): The question to process.
        """
        # Switch current most probable answer to second most probable
        # Get current most probable answers
        most_probable_answer1: Answer = question.data[self.name]["most_probable_answer1"]
        most_probable_answer2: Answer = question.data[self.name]["most_probable_answer2"]
        # Decrease counter of current most probable answer to zero
        most_probable_answer1.data[self.name]["most_probable1"] = False
        most_probable_answer1.data[self.name]["counter1"] = 0
        # Set most probable answer 1 to most probable answer 2
        most_probable_answer1 = most_probable_answer2
        most_probable_answer1.data[self.name]["most_probable1"] = True
        most_probable_answer1.data[self.name]["counter1"] = 1
        # Update question data
        question.data[self.name]["most_probable_answer1"] = most_probable_answer1
        # Change second most probable answer to a new random answer
        self._change_most_probable_answer2(question)

    def _change_most_probable_answer2(self, question: 'Question'):
        """
        Change the most probable answer for a question.
        Args:
            question (Question): The question to process.
        """
        most_probable_answer1: Answer = question.data[self.name]["most_probable_answer1"]
        # Get list of possible answers to select from
        possible_answers = []
        for answer in question.answers:
            #if answer.is_correct is None and answer != most_probable_answer:
            if answer.is_correct is None and answer != most_probable_answer1:
                possible_answers.append(answer)
        # this should never happen        
        if len(possible_answers) < 2:
            raise ValueError("No possible answers to select from in strategy Beta / NegativeBeta. "
                             "This should not happen.")
        # Select a new most probable answer randomly from possible answers
        # and initialize its data
        new_most_probable_answer = random.choice(possible_answers)
        new_most_probable_answer.data[self.name]["most_probable2"] = True
        new_most_probable_answer.data[self.name]["counter2"] = 1
        # Update question data
        question.data[self.name]["most_probable_answer2"] = new_most_probable_answer
        # Reset data for other answers
        for answer in question.answers:
            if answer != new_most_probable_answer:
                answer.data[self.name]["most_probable2"] = False
                answer.data[self.name]["counter2"] = 0
    
    def increase_counter(self, question: 'Question', group_index: str):
        """
        Increase the counter for the most probable answer of a question.
        Args:
            question (Question): The question to process.
            group_index (str): The group index ("1" or "2") to determine which counter to increase.
        """
        most_probable_answer: Answer = question.data[self.name][f"most_probable_answer{group_index}"]
        most_probable_answer.data[self.name][f"counter{group_index}"] += 1

    def decrease_counter(self, question: 'Question', group_index: str):
        """
        Decrease the counter for the most probable answer of a question.
        Args:
            question (Question): The question to process.
            group_index (str): The group index ("1" or "2") to det ermine which counter to decrease.
        """
        most_probable_answer: Answer = question.data[self.name][f"most_probable_answer{group_index}"]
        most_probable_answer.data[self.name][f"counter{group_index}"] -= 1
        # Change most probable answer if counter is zero or negative
        if most_probable_answer.data[self.name][f"counter{group_index}"] <= epsilon:
            if group_index == "1":
                self._change_most_probable_answer1(question)
            else:
                self._change_most_probable_answer2(question)

    def _initialize_moving_average(self):
        """
        Initialize the moving average for tracking score changes.
        """
        # if moving average 1 is not initialized
        if self._ma1 is None or self._ma2 is None or self._ma0 is None:
            # compute initial average probability
            probability = []
            for question in self._quizsolver._latest_quiz:
                probability.append(1 / len(question.answers))
            average_probability = sum(probability) / len(probability)
            # initialize moving average
            self._ma0 = MovingAverage(initial_value=average_probability)
            self._ma1 = MovingAverage(initial_value=average_probability)
            self._ma2 = MovingAverage(initial_value=average_probability)

    def _update_moving_average_window_size(self):
        """
        Update the moving average window size based on the current epoch.
        """
        epoch = self._quizsolver.epoch
        ma0_window_size = 10
        ma1_ma2_window_size = 5
        if (epoch & (epoch - 1)) == 0 and \
            self._ma0 is not None and \
            self._ma1 is not None and \
            self._ma2 is not None:
            if self._ma0.window_size != ma0_window_size:
                self._ma0.set_window_size(ma0_window_size)
            if self._ma1.window_size != ma1_ma2_window_size:
                self._ma1.set_window_size(ma1_ma2_window_size)
            if self._ma2.window_size != ma1_ma2_window_size:
                self._ma2.set_window_size(ma1_ma2_window_size)
            # window_size = self._quizsolver._calculate_moving_average_window_size() + 10
            # if self._ma0.window_size != window_size:
            #     self._ma0.set_window_size(window_size)
            # if self._ma1.window_size != window_size:
            #     self._ma1.set_window_size(3)
            # if self._ma2.window_size != window_size:
            #     self._ma2.set_window_size(3)

    def process_quiz_feedback(self, *, score: float, max_score: float):
        """
        Process feedback after a quiz has been submitted and scored.
        Args:
            score (float): The score received for the submitted quiz.
        """
        # compute score factor
        factor = score / max_score
        # store latest score and max score
        self.latest_score = score
        self.latest_max_score = max_score
        # normalize counters across all questions
        #self.normalize_counters_across_all_questions()
        # Initialize and update moving average
        self._initialize_moving_average()
        if self._ma0 is None or self._ma1 is None or self._ma2 is None:
            raise ValueError("Moving average not initialized.")
        self._update_moving_average_window_size()
        # Update moving averages with current factor
        if self.epochs_used % 2 == 0:
            self._ma1.add_value(factor)
        else:
            self._ma2.add_value(factor)
        # Update epoch count
        self.epochs_used += 1
        # if this is not the right epoch to update, return
        capturing_data = self._ma1.window_size + self._ma2.window_size + self.window_size_delta
        if self.epochs_used % capturing_data != 0:
            return
        # Update moving average with current measurement
        ma1_median = self._ma1.median
        ma2_median = self._ma2.median
        #self._ma0.add_value((ma1_median + ma2_median) / 2)
        #self._ma0.add_value(max(ma1_median, ma2_median))
        self._ma0.add_value(ma1_median)
        threshold = self._ma0.moving_average
        # train answer probabilities
        for question in self.training_minibatch:
            # If question is already solved then continue
            if question.is_solved:
                continue
            # select most probable answer
            most_probable_answer1: Answer = question.data[self.name]["most_probable_answer1"]
            most_probable_answer2: Answer = question.data[self.name]["most_probable_answer2"]
            # If the most probable answer is marked as incorrect, change it
            correctness_modified = False
            if most_probable_answer2.is_correct == False:
                self._change_most_probable_answer2(question)
                correctness_modified = True
            if most_probable_answer1.is_correct == False:
                self._change_most_probable_answer1(question)
                correctness_modified = True
            if correctness_modified:
                continue
            #Update counters counters of group 1
            # if ma1_median > ma2_median and ma1_median > ma0_average:
            #     self.increase_counter(question, group_index="1")
            # elif ma1_median < ma2_median:
            #     self.decrease_counter(question, group_index="1")

            # if ma2_median > ma0_average:
            #     self.increase_counter(question, group_index="2")
            # else:
            #     self.decrease_counter(question, group_index="2")

            # if ma1_median - epsilon > ma0_average:
            #     self.increase_counter(question, group_index="1")
            # else:
            #     self.decrease_counter(question, group_index="1")

            # if ma2_median - epsilon > ma0_average:
            #     self.increase_counter(question, group_index="2")
            # else:
            #     self.decrease_counter(question, group_index="2")

            # if ma1_median - epsilon < ma2_median:
            #     self.decrease_counter(question, group_index="1")
            # elif ma1_median - epsilon > threshold:
            #     self.increase_counter(question, group_index="1")
            #     self.decrease_counter(question, group_index="2")
            # else:
            #     self.decrease_counter(question, group_index="2")

            m1 = ma1_median - epsilon * random.uniform(0, 1)
            m2 = ma2_median - epsilon * random.uniform(0, 1)
            threshold = threshold - epsilon * random.uniform(0, 1)
            if self.is_negative == False:
                if m1 > m2 > threshold:
                    self.increase_counter(question, group_index="1")
                    #self.decrease_counter(question, group_index="2")
                elif m2 > m1 > threshold:
                    self.increase_counter(question, group_index="2")
                    self.decrease_counter(question, group_index="1")
                elif m2 > threshold > m1:
                    self.increase_counter(question, group_index="2")
                    self.decrease_counter(question, group_index="1")
                elif m1 > threshold > m2:
                    self.increase_counter(question, group_index="1")
                    self.decrease_counter(question, group_index="2")
                elif threshold > m1 > m2:
                    #self.decrease_counter(question, group_index="1")
                    self.decrease_counter(question, group_index="2")
                elif threshold > m2 > m1:
                    #self.decrease_counter(question, group_index="2")
                    self.decrease_counter(question, group_index="1")
            else:
                if m1 > m2 > threshold:
                    self.decrease_counter(question, group_index="1")
                    #self.decrease_counter(question, group_index="2")
                elif m2 > m1 > threshold:
                    self.decrease_counter(question, group_index="2")
                    self.increase_counter(question, group_index="1")
                elif m2 > threshold > m1:
                    self.decrease_counter(question, group_index="2")
                    self.increase_counter(question, group_index="1")
                elif m1 > threshold > m2:
                    self.decrease_counter(question, group_index="1")
                    self.increase_counter(question, group_index="2")
                elif threshold > m1 > m2:
                    self.decrease_counter(question, group_index="1")
                    self.increase_counter(question, group_index="2")
                elif threshold > m2 > m1:
                    self.increase_counter(question, group_index="2")
                    self.increase_counter(question, group_index="1")
        self.finished_measurements += 1
        self.pick_training_minibatch(how_many_to_pick = 1)
        #self.pick_training_group()
        # if self.finished_measurements % 100 == 0:
        #     self.plot()
    
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
        answers_per_row = 200
        max_answers = rows * answers_per_row
        # Initialize figure and axes if not already done
        if not self.figure_initialized:
            self.figure, self.axes = plt.subplots(rows, cols, figsize=(14, 9))
            self.figure_initialized = True
            # initialize axes data
            for row in range(rows):
                self.axes_data.append([])
        # Check if moving averages are initialized
        if self._ma0 is None or self._ma1 is None or self._ma2 is None:
            return
        # Clear and update first subplot
        self.axes[0].clear()
        self.axes[0].set_title(f'Strategy {self.name}. '
                               f'Avg0: {self._ma0.moving_average:.4f}, '
                               f'Med1: {self._ma1.moving_average:.4f}, '
                               f'Med2: {self._ma2.moving_average:.4f}')
        self.axes[0].plot(self._ma0.history_of_moving_averages, label='MA0 Moving Average', color='blue')
        self.axes[0].plot(self._ma1.history_of_medians, label='MA1 Median', color='cyan')
        self.axes[0].plot(self._ma2.history_of_medians, label='MA2 Median', color='orange')
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
            if answers_count >= max_answers:
                break
            is_in_training_group = question in self.training_group
            for answer in question.answers:
                if answers_count >= max_answers:
                    break
                if answer.data[self.name]["counter1"] > 0:
                    colors.append('blue' if is_in_training_group else 'black')
                    answers.append(answer.data[self.name]["counter1"])
                elif answer.data[self.name]["counter2"] > 0:
                    colors.append('cornflowerblue' if is_in_training_group else 'gray')
                    answers.append(answer.data[self.name]["counter2"])
                else:
                    colors.append('lightgray')
                    answers.append(0.5)
            # increment answers count
            answers_count += len(question.answers) + 2
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
            self.axes[i].bar(range(len(data)), data, color=color_data, alpha=0.7)


        # questions = list(self._quizsolver.questions.values())
        # x = list(range(len(questions)))
        # colors = ['blue' if question in self.training_group else 'black' for question in questions]
        # for i in range(1, 5):
        #     self.axes[i].clear()
        #     #self.axes[i].set_title(f'Probabilities of Answer {i}')
        #     probabilities = []
        #     for question in questions:
        #         if question.most_probable_answer_index == i - 1:
        #             probabilities.append(question.most_probable_answer.probability)
        #         else:
        #             probabilities.append(0.0)
        #     self.axes[i].bar(x, probabilities, color=colors, alpha=0.7)
        plt.pause(0.1)
        
    
    # def print_statistics(self) -> str:
    #     """
    #     Print statistics related to the strategy's performance.
    #     """
    #     # return statistics
    #     factor = self.latest_score / self.latest_max_score if self.latest_max_score > 0 else 0.0
    #     window_size = self._ma0.window_size if self._ma0 else 0
    #     moving_average = self._ma0.moving_average if self._ma0 else 0.0
    #     result = f"Strategy {self.name}:\n"
    #     result += f"  Enabled: {self.enabled}\n"
    #     result += f"  Epochs used: {self.epochs_used}\n"
    #     result += f"  Finished Measurements: {self.finished_measurements}\n"
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
        window_size = self._ma0.window_size if self._ma0 else 0
        moving_average = self._ma0.moving_average if self._ma0 else 0.0
        result = f'Strategy {self.name} ({"Enabled" if self.enabled else "Disabled"}):\n'
        result += f'  Measurements Finished / Epochs used: {self.finished_measurements} / {self.epochs_used}\n'
        result += f'  Moving Average: {moving_average * 100:,.3f}% (Window Size={window_size})\n'
        # draw progress bar
        bar_length = 50
        factor2 = factor
        bar_used = int(factor2 * bar_length)
        result += f"[" + "#" * bar_used + "-" * (bar_length - bar_used) + "]\n"
        return result