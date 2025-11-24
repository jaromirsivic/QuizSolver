import matplotlib.pyplot as plt

class MovingAverage:
    def __init__(self, *, initial_value: float = 0.0, window_size: int = 32, max_window_size: int = 10000):
        """
        Initialize the MovingAverage with a specified window size.
        Args:
            window_size (int): The size of the moving average window.
            max_window_size (int): The maximum size of the internal storage.
            initial_value (float): The initial value to fill the window.
        """
        self.window_size: int = window_size
        self.max_window_size = max_window_size
        self.values: list[float] = [initial_value] * max_window_size
        self.values_weights: list[float] = [1.0] * max_window_size
        self.index = 0
        self.cumulative_sum = initial_value * window_size
        # For plotting history
        self.history_figure_initialized = False
        self.history_figure = None
        self.history_of_moving_averages: list[float] = []
        self.history_of_medians: list[float] = []

    def add_value(self, value: float, value_weight: float = 1.0) -> None:
        """
        Add a new value to the moving average calculation.
        Args:
            value (float): The new value to add.
        Returns:
            float: The updated moving average.
        """
        # Update cumulative sum
        old_index = (self.index - self.window_size) % self.max_window_size
        self.cumulative_sum += (value * value_weight) - (self.values[old_index] * self.values_weights[old_index])
        self.values[self.index] = value
        self.values_weights[self.index] = value_weight
        self.index = (self.index + 1) % self.max_window_size
        # Record history
        len_history_of_moving_averages = len(self.history_of_moving_averages)
        if len_history_of_moving_averages < self.max_window_size:
            self.history_of_moving_averages.append(self.moving_average)
            self.history_of_medians.append(self.median)
        else:
            self.history_of_moving_averages[len_history_of_moving_averages % self.max_window_size] = self.moving_average
            self.history_of_medians[len_history_of_moving_averages % self.max_window_size] = self.median

    def reset(self):
        """
        Reset the moving average to its initial state.
        """
        self.values = [0.0] * self.max_window_size
        self.values_weights = [1.0] * self.max_window_size
        #self.index = 0
        self.cumulative_sum = 0.0
        #self.history_of_moving_averages.clear()
        #self.history_of_medians.clear()
    
    @property
    def moving_average(self) -> float:
        """
        Get the current moving average.
        Returns:
            float: The current moving average.
        """
        return self.cumulative_sum / self.window_size
        total_weight = sum(self.values_weights[(self.index - i - 1) % self.max_window_size] for i in range(self.window_size))
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(self.values[(self.index - i - 1) % self.max_window_size] * \
                           self.values_weights[(self.index - i - 1) % self.max_window_size] \
                           for i in range(self.window_size))
        return weighted_sum / total_weight
    
    @property
    def median(self) -> float:
        """
        Get the median of the current values in the moving average window.
        Returns:
            float: The median value.
        """
        relevant_values = [self.values[(self.index - i - 1) % self.max_window_size] for i in range(self.window_size)]
        sorted_values = sorted(relevant_values)
        mid = self.window_size // 2
        if self.window_size % 2 == 0:
            return (sorted_values[mid - 1] + sorted_values[mid]) / 2.0
        else:
            return sorted_values[mid]
        
    # def plot_history(self):
    #     """
    #     Plot the history of moving averages and medians.
    #     """
    #     if not self.history_figure_initialized:
    #         self.history_figure = plt.figure(figsize=(10, 5))
    #         self.history_figure_initialized = True
        
    #     plt.ion()
    #     plt.clf()
    #     plt.plot(self.history_of_moving_averages, label='Moving Average', color='blue')
    #     plt.plot(self.history_of_medians, label='Median', color='orange')
    #     plt.xlabel('Epochs')
    #     plt.ylabel('Value')
    #     plt.title('Moving Average and Median History')
    #     plt.legend()
    #     plt.grid(True)
    #     plt.pause(0.01)  # Pause to update the plot
    
    def set_window_size(self, new_window_size: int):
        """
        Set a new window size for the moving average.
        Args:
            new_window_size (int): The new window size to set.
        """
        if new_window_size > self.max_window_size:
            raise ValueError(f'New window size {new_window_size} exceeds maximum of {self.max_window_size}.')
        if new_window_size < self.window_size:
            # Adjust cumulative sum when reducing window size
            for i in range(self.window_size - new_window_size):
                self.cumulative_sum -= self.values[(self.index - self.window_size + i) % self.max_window_size]
        else:
            # Adjust cumulative sum when increasing window size
            for i in range(new_window_size - self.window_size):
                self.cumulative_sum += self.values[(self.index - new_window_size + i) % self.max_window_size]
        # Update the window size
        self.window_size = new_window_size