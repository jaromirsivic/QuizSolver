import json
import argparse
from package.quizsolver import *


def run_quizsolver():
    # Parse command-line arguments
    # There is an argument "strategy" to choose the strategy in use
    parser = argparse.ArgumentParser(description="Quiz Solver")
    parser.add_argument("--strategy", type=str, default="A4", help="Strategy to use for solving the quiz")
    args = parser.parse_args()

    quiz_setup = QuizSolverSetup()
    quiz_generator = QuizGenerator(questions_count=500, 
                                   min_answers_per_question=4, 
                                   max_answers_per_question=4,
                                   probability_of_choose_one_type=1.0,
                                   probability_of_choose_one_or_more_type=0.0,
                                   probability_of_choose_zero_or_more_type=0.0)
    quiz_solver = QuizSolver(quiz_setup=quiz_setup, strategy_in_use=args.strategy)

    print("Generating Quiz...")
    print(json.dumps(quiz_generator.questions_dict, indent=4))

    quiz_solved: dict = {"finished": False}

    while not quiz_solved["finished"]:
        quiz_questions_multiplier = 0.9
        quiz_questions_count = max(1, int(quiz_questions_multiplier * quiz_generator.questions_count))   
        quiz = quiz_generator.generate_quiz(num_questions=quiz_questions_count)
        #quiz_raw_questions = list(question["question"] for question in quiz["questions"])
        #print("Quiz Questions:")
        # print(json.dumps(quiz, indent=4))

        solved_questions = []
        for raw_question in quiz["questions"]:
            solved_questions.append(quiz_solver.give_answer(quiz_question=raw_question))
        solved_quiz = {"questions": solved_questions}
        #solved_quiz_raw_questions = list(question["question"] for question in solved_quiz["questions"])
        #print("Solved Quiz:")
        # print(json.dumps(solved_quiz, indent=4))

        score = quiz_generator.compute_score(quiz=solved_quiz)            
        #print(f"Score: {score}")

        quiz_solved = quiz_solver.process_score_feedback(score=score, max_score = 1.0)
        # if score == 1:
        #     break
    
    print("Quiz Solved!")
    print(json.dumps(quiz_solved, indent=4))
    return quiz_solved["epoch"]


if __name__ == "__main__":
    result = []
    for i in range(1):
        result.append(run_quizsolver())
    print(sorted(result))