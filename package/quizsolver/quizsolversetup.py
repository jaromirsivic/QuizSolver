from .rawquestion import RawQuestion


class QuizSolverSetup:
    def __init__(self, *, max_epochs: int = 10000000,
                 moving_average_window_size: int | None = None):
        self.max_epochs = max_epochs
        self.max_probability = 100000
        self.moving_average_window_size = moving_average_window_size
        