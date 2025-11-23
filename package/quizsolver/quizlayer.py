from .quizsolver import QuizSolver
from .question import Question
from .answer import Answer


class QuizLayer:
    def __init__(self, parent_quizsolver: 'QuizSolver'):
        self.parent_quizsolver = parent_quizsolver
        self.questions: list[Question] = []
        self.question_uid_map: dict[str, Question] = {}

    def add_question(self, question: Question):
        self.questions.append(question)
        self.question_uid_map[question.uid] = question
    
    def solve(self, quiz: dict) -> dict:
        return quiz