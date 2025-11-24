import datetime
from .rawquestion import RawQuestion


class QuizSolverStatistics(dict):
    def __init__(self):
        super().__init__()
        self["started_at"] = datetime.datetime.now()
        self["finished_at"] = None
        self["epochs"] = 0
        self["min_score"] = None
        self["min_score_epoch"] = None
        self["max_score"] = None
        self["max_score_epoch"] = None
        self["questions_total"] = 0
        self["answers_total"] = 0
        self["questions_per_quiz_on_average"] = 0.0
        self["answers_per_quiz_on_average"] = 0.0
        self["sum_of_all_questions_of_all_quizzes"] = 0
        self["sum_of_all_answers_of_all_quizzes"] = 0   
        