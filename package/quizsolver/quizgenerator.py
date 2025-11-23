import random
from .common import RawQuestionType


class QuizGenerator:
    def __init__(self, *, questions_count: int = 200,
                 min_answers_per_question: int = 4,
                 max_answers_per_question: int = 4, 
                 probability_of_choose_one_type: float = 1.0,
                 probability_of_choose_one_or_more_type: float = 0.0, 
                 probability_of_choose_zero_or_more_type: float = 0.0):
        """
        Initialize the QuizGenerator with a specified number of questions.
        Each question will have a random number of answers between min_answers and max_answers.
        """
        # Initialize internal data structures
        self.questions_count = questions_count
        self.questions_dict: dict = {}
        self.questions_list: list[dict] = []
        total_probability = (probability_of_choose_one_type +
                             probability_of_choose_one_or_more_type +
                             probability_of_choose_zero_or_more_type)
        # Generate questions
        for i in range(questions_count):
            num_answers = random.randint(min_answers_per_question, max_answers_per_question)
            random_value = random.uniform(0, total_probability)
            question_type = None
            if random_value < probability_of_choose_one_type:
                correct_answer_indexes = [random.randint(0, num_answers - 1)]
                question_type = RawQuestionType.CHOOSE_ONE.value
            elif random_value < (probability_of_choose_one_type + probability_of_choose_one_or_more_type):
                correct_answer_indexes = random.sample(range(num_answers), random.randint(1, num_answers))
                question_type = RawQuestionType.CHOOSE_ONE_OR_MORE.value
            else:
                correct_answer_indexes = random.sample(range(num_answers), random.randint(0, num_answers))
                question_type = RawQuestionType.CHOOSE_ZERO_OR_MORE.value
            # Generate answers
            answers = []
            for j in range(num_answers):
                if j in correct_answer_indexes:
                    answers.append({
                        "answer": f"1 * {i} ~= {i + random.uniform(0.1111, 0.11119)}",
                        "correct": True
                    })
                else:
                    answers.append({
                        "answer": f"1 * {i} ~= {i + random.randint(1, 1000) + random.uniform(0.0, 0.00009)}",
                        "correct": False
                    })
            # Generate question
            question = {
                "question": f"1 * {i} ~= ?",
                "answers": answers,
                "type": question_type
            }
            # Store question in both dict and list
            self.questions_dict[f"1 * {i} ~= ?"] = question
            self.questions_list.append(question)

    def generate_quiz(self, *, num_questions: int) -> dict:
        """
        Get a quiz with the specified number of questions.
        Questions are randomly selected from the questions_dict.
        Parameter is_corrrect is removed from the result.
        """
        if num_questions > self.questions_count:
            raise ValueError("Requested number of questions exceeds available questions.")
        # Randomly select questions
        selected_questions = random.sample(self.questions_list, num_questions)
        quiz = {"questions": []}
        # Prepare quiz structure without 'correct' field
        for q in selected_questions:
            question_copy = {
                "question": q["question"],
                "answers": [{"answer": a["answer"]} for a in q["answers"]]
            }
            quiz["questions"].append(question_copy)
        return quiz
    
    def compute_score(self, *, quiz: dict) -> float:
        """
        Calculate the score of the quiz based on correct answers.
        Score is the ratio of correctly answered questions to total questions.
        Parameters:
            quiz (dict): The quiz structure with user's answers including 'correct' fields.
        Returns:
            float: The score as a float between 0 and 1.
        """
        correctly_answered = 0
        # Evaluate each question
        for q in quiz["questions"]:
            original_question = self.questions_dict[q["question"]]
            answer_is_valid = True
            # Check each answer
            for given_answer_index, given_answer in enumerate(q["answers"]):
                if given_answer["correct"] != original_question["answers"][given_answer_index]["correct"]:
                    answer_is_valid = False
                    break
            # If all answers are correct, increment the count
            if answer_is_valid:
                correctly_answered += 1
        # Calculate score
        score = correctly_answered / len(quiz["questions"])
        return score          