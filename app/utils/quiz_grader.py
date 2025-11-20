"""
Quiz grading utilities.

This module provides functions for grading quiz answers, calculating scores,
and generating feedback.
"""


def grade_single_choice(question, user_answer):
    """
    Grade a single choice question.
    
    Args:
        question: Question model instance
        user_answer: Single answer index selected by user
        
    Returns:
        dict: {
            'correct': bool,
            'points_earned': int,
            'correct_answers': list of correct answer indices,
            'user_answers': list of user's answer indices
        }
    """
    if question.question_type != 'single_choice':
        raise ValueError("Question type must be 'single_choice'")
    
    correct_answers = question.correct_answers
    user_answers = [user_answer] if isinstance(user_answer, int) else user_answer
    
    # For single choice, must select exactly one correct answer
    is_correct = (
        len(user_answers) == 1 and
        user_answers[0] in correct_answers
    )
    
    points_earned = question.points if is_correct else 0
    
    return {
        'correct': is_correct,
        'points_earned': points_earned,
        'correct_answers': correct_answers,
        'user_answers': user_answers
    }


def grade_multiple_choice(question, user_answers):
    """
    Grade a multiple choice question (can have multiple correct answers).
    
    Args:
        question: Question model instance
        user_answers: List of answer indices selected by user
        
    Returns:
        dict: {
            'correct': bool,
            'points_earned': int,
            'correct_answers': list of correct answer indices,
            'user_answers': list of user's answer indices
        }
    """
    if question.question_type != 'multiple_choice':
        raise ValueError("Question type must be 'multiple_choice'")
    
    correct_answers = set(question.correct_answers)
    user_answer_set = set(user_answers if isinstance(user_answers, list) else [user_answers])
    
    # For multiple choice, must select all correct answers and no incorrect ones
    is_correct = user_answer_set == correct_answers
    
    points_earned = question.points if is_correct else 0
    
    return {
        'correct': is_correct,
        'points_earned': points_earned,
        'correct_answers': list(correct_answers),
        'user_answers': list(user_answer_set)
    }


def calculate_total_score(attempt):
    """
    Calculate total score for a quiz attempt.
    
    Args:
        attempt: QuizAttempt model instance
        
    Returns:
        dict: {
            'score_percentage': float (0-100),
            'points_earned': int,
            'total_points': int,
            'questions_correct': int,
            'total_questions': int
        }
    """
    if not attempt.quiz:
        return {
            'score_percentage': 0,
            'points_earned': 0,
            'total_points': 0,
            'questions_correct': 0,
            'total_questions': 0
        }
    
    points_earned = 0
    total_points = 0
    questions_correct = 0
    total_questions = 0
    
    # Get quiz instance data if available
    quiz_instance = attempt.answers_given.get('_quiz_instance', {})
    selected_question_ids = quiz_instance.get('question_ids', [])
    
    # If no quiz instance, use all questions in quiz
    if selected_question_ids:
        questions = [q for q in attempt.quiz.questions if q.id in selected_question_ids]
    else:
        questions = attempt.quiz.questions.all()
    
    for question in questions:
        total_points += question.points
        total_questions += 1
        
        # Get user's answer for this question
        user_answer = attempt.answers_given.get(str(question.id))
        
        if user_answer is None:
            continue
        
        # Grade the question based on type
        if question.question_type == 'single_choice':
            result = grade_single_choice(question, user_answer)
        else:
            result = grade_multiple_choice(question, user_answer)
        
        points_earned += result['points_earned']
        if result['correct']:
            questions_correct += 1
    
    # Calculate percentage
    score_percentage = (points_earned / total_points * 100) if total_points > 0 else 0
    
    return {
        'score_percentage': round(score_percentage, 2),
        'points_earned': points_earned,
        'total_points': total_points,
        'questions_correct': questions_correct,
        'total_questions': total_questions
    }


def generate_feedback(attempt):
    """
    Generate detailed feedback for a quiz attempt with explanations.
    
    Args:
        attempt: QuizAttempt model instance
        
    Returns:
        dict: {
            'overall': dict with score summary,
            'questions': list of question feedback with explanations
        }
    """
    score_data = calculate_total_score(attempt)
    
    questions_feedback = []
    
    # Get quiz instance data if available
    quiz_instance = attempt.answers_given.get('_quiz_instance', {})
    selected_question_ids = quiz_instance.get('question_ids', [])
    
    # If no quiz instance, use all questions in quiz
    if selected_question_ids:
        questions = [q for q in attempt.quiz.questions if q.id in selected_question_ids]
    else:
        questions = attempt.quiz.questions.all()
    
    for question in questions:
        user_answer = attempt.answers_given.get(str(question.id))
        
        # Grade the question
        if question.question_type == 'single_choice':
            result = grade_single_choice(question, user_answer) if user_answer is not None else {
                'correct': False,
                'points_earned': 0,
                'correct_answers': question.correct_answers,
                'user_answers': []
            }
        else:
            result = grade_multiple_choice(question, user_answer) if user_answer is not None else {
                'correct': False,
                'points_earned': 0,
                'correct_answers': question.correct_answers,
                'user_answers': []
            }
        
        # Build feedback for this question
        feedback = {
            'question_id': question.id,
            'question_text': question.question_text,
            'question_type': question.question_type,
            'correct': result['correct'],
            'points_earned': result['points_earned'],
            'points_possible': question.points,
            'user_answers': result['user_answers'],
            'correct_answers': result['correct_answers'],
            'explanations': []
        }
        
        # Add explanations for answers
        if question.answers:
            for idx, answer in enumerate(question.answers):
                if answer.get('explanation'):
                    feedback['explanations'].append({
                        'answer_index': idx,
                        'answer_text': answer.get('text', ''),
                        'explanation': answer.get('explanation'),
                        'is_correct': idx in result['correct_answers']
                    })
        
        questions_feedback.append(feedback)
    
    return {
        'overall': {
            'score_percentage': score_data['score_percentage'],
            'points_earned': score_data['points_earned'],
            'total_points': score_data['total_points'],
            'questions_correct': score_data['questions_correct'],
            'total_questions': score_data['total_questions'],
            'passed': determine_pass_fail(score_data['score_percentage'], attempt.quiz.minimum_score)
        },
        'questions': questions_feedback
    }


def determine_pass_fail(score, minimum_score):
    """
    Determine if a score meets the minimum passing threshold.
    
    Args:
        score: Score percentage (0-100)
        minimum_score: Minimum passing score percentage (0-100)
        
    Returns:
        bool: True if passed, False if failed
    """
    return score >= minimum_score
