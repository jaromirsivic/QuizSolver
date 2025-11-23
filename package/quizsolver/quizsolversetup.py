from .rawquestion import RawQuestion


class QuizSolverSetup(dict):
    def __init__(self, *, targeted_score: float = 0.95, max_epochs: int = 10000000,
                 redraw_console_interval: float = 0.25, render_plots_interval: float = -1,
                 preferred_strategy: str | None = None,
                 moving_average_window_size_override: int | None = None,
                 measurement_rounds_of_beta_strategies: int = 1):
        super().__init__()
        self["targeted_score"] = targeted_score
        self["max_epochs"] = max_epochs
        self["redraw_console_interval"] = redraw_console_interval
        self["render_plots_interval"] = render_plots_interval
        self["preferred_strategy"] = preferred_strategy
        self["moving_average_window_size_override"] = moving_average_window_size_override
        self["measurement_rounds_of_beta_strategies"] = measurement_rounds_of_beta_strategies

    @property
    def targeted_score(self) -> float:
        """
        Get the targeted score for the quiz solver.
        """
        return self.get("targeted_score", 0.95)
    
    @targeted_score.setter
    def targeted_score(self, value: float):
        """
        Set the targeted score for the quiz solver.
        """
        self["targeted_score"] = value

    @property
    def max_epochs(self) -> int:
        """
        Get the maximum number of epochs for the quiz solver.
        """
        return self.get("max_epochs", 10000000)
    
    @max_epochs.setter
    def max_epochs(self, value: int):
        """
        Set the maximum number of epochs for the quiz solver.
        """
        self["max_epochs"] = value

    @property
    def redraw_console_interval(self) -> float:
        """
        Get the interval for redrawing the console.
        """
        return self.get("redraw_console_interval", 0.25)
    
    @redraw_console_interval.setter
    def redraw_console_interval(self, value: float):
        """
        Set the interval for redrawing the console.
        """
        self["redraw_console_interval"] = value

    @property
    def render_plots_interval(self) -> float:
        """
        Get the interval for rendering plots.
        """
        return self.get("render_plots_interval", -1)
    
    @render_plots_interval.setter
    def render_plots_interval(self, value: float):
        """
        Set the interval for rendering plots.
        """
        self["render_plots_interval"] = value

    @property
    def moving_average_window_size_override(self) -> int | None:
        """
        Get the moving average window size override if set.
        Moving average window size override takes precedence over the computed moving average window size
        in strategies Alpha, NegativeAlpha, Beta, and NegativeBeta.
        """
        return self.get("moving_average_window_size_override", None)
    
    @moving_average_window_size_override.setter
    def moving_average_window_size_override(self, value: int | None):
        """
        Set the moving average window size override.
        Moving average window size override takes precedence over the computed moving average window size
        in strategies Alpha, NegativeAlpha, Beta, and NegativeBeta.
        """
        self["moving_average_window_size_override"] = value
    
    @property
    def measurement_rounds_of_beta_strategies(self) -> int:
        """
        Get the number of measurement rounds for Beta and NegativeBeta strategies.
        """
        return self.get("measurement_rounds_of_beta_strategies", 1)
    
    @measurement_rounds_of_beta_strategies.setter
    def measurement_rounds_of_beta_strategies(self, value: int):
        """
        Set the number of measurement rounds for Beta and NegativeBeta strategies.
        """
        self["measurement_rounds_of_beta_strategies"] = value

    
        