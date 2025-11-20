"""
Service for managing quiz attempts.

This module provides functions for creating, updating, and grading quiz attempts.
"""

from datetime import datetime
from app import db
from app.models import QuizAttempt, Quiz
from app.utils.quiz_grader import calculate_total_score, generate_feedback, determine_pass_fail


def start_attempt(user_id, quiz_id, quiz_instance):
    """
    Initialize a new quiz attempt.
    
    Args:
        user_id: ID of the user taking the quiz
        quiz_id: ID of the quiz
        quiz_instance: Dictionary from generate_quiz_instance containing
                      randomized questions and quiz_hash
                      
    Returns:
        tuple: (QuizAttempt instance, error_message)
    """
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return None, "Quiz introuvable."
    
    try:
        # Initialize answers_given with quiz instance data
        answers_given = {
            '_quiz_instance': {
                'quiz_id': quiz_instance['quiz_id'],
                'question_ids': quiz_instance['question_ids'],
                'quiz_hash': quiz_instance['quiz_hash']
            }
        }
        
        attempt = QuizAttempt(
            user_id=user_id,
            quiz_id=quiz_id,
            answers_given=answers_given,
            score=0,
            passed=False,
            started_at=datetime.utcnow()
        )
        
        db.session.add(attempt)
        db.session.commit()
        
        return attempt, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors du démarrage de la tentative: {str(e)}"


def submit_answer(attempt_id, question_id, answer):
    """
    Save a single answer for a quiz attempt.
    
    Args:
        attempt_id: ID of the quiz attempt
        question_id: ID of the question being answered
        answer: Answer data (int for single choice, list for multiple choice)
        
    Returns:
        tuple: (QuizAttempt instance, error_message)
    """
    attempt = QuizAttempt.query.get(attempt_id)
    
    if not attempt:
        return None, "Tentative introuvable."
    
    if attempt.is_completed:
        return None, "Cette tentative est déjà terminée."
    
    try:
        # Update answers_given with the new answer
        answers = attempt.answers_given.copy()
        answers[str(question_id)] = answer
        
        # Update the attempt
        attempt.answers_given = answers
        
        # Mark as modified to trigger SQLAlchemy update
        db.session.add(attempt)
        db.session.commit()
        
        return attempt, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de l'enregistrement de la réponse: {str(e)}"


def complete_attempt(attempt_id):
    """
    Finalize and grade a quiz attempt.
    
    Args:
        attempt_id: ID of the quiz attempt
        
    Returns:
        tuple: (QuizAttempt instance with results, error_message)
    """
    attempt = QuizAttempt.query.get(attempt_id)
    
    if not attempt:
        return None, "Tentative introuvable."
    
    if attempt.is_completed:
        return None, "Cette tentative est déjà terminée."
    
    try:
        # Mark as completed
        attempt.completed_at = datetime.utcnow()
        
        # Calculate time taken
        if attempt.started_at and attempt.completed_at:
            time_delta = attempt.completed_at - attempt.started_at
            attempt.time_taken = int(time_delta.total_seconds())
        
        # Grade the attempt
        grading_result = grade_attempt(attempt)
        
        # Update score and passed status
        attempt.score = grading_result['score_percentage']
        attempt.passed = grading_result['passed']
        
        db.session.commit()
        
        return attempt, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de la finalisation de la tentative: {str(e)}"


def grade_attempt(attempt):
    """
    Calculate score and determine pass/fail status for an attempt.
    
    Args:
        attempt: QuizAttempt instance
        
    Returns:
        dict: {
            'score_percentage': float,
            'points_earned': int,
            'total_points': int,
            'questions_correct': int,
            'total_questions': int,
            'passed': bool
        }
    """
    score_data = calculate_total_score(attempt)
    
    # Determine if passed
    passed = determine_pass_fail(
        score_data['score_percentage'],
        attempt.quiz.minimum_score
    )
    
    return {
        'score_percentage': score_data['score_percentage'],
        'points_earned': score_data['points_earned'],
        'total_points': score_data['total_points'],
        'questions_correct': score_data['questions_correct'],
        'total_questions': score_data['total_questions'],
        'passed': passed
    }


def get_attempt_results(attempt_id):
    """
    Retrieve detailed results for a quiz attempt with explanations.
    
    Args:
        attempt_id: ID of the quiz attempt
        
    Returns:
        dict: {
            'attempt': QuizAttempt instance,
            'feedback': dict from generate_feedback with detailed results
        }
        or None if not found
    """
    attempt = QuizAttempt.query.get(attempt_id)
    
    if not attempt:
        return None
    
    if not attempt.is_completed:
        return {
            'attempt': attempt,
            'feedback': None,
            'error': 'Tentative non terminée'
        }
    
    # Generate feedback
    feedback = generate_feedback(attempt)
    
    return {
        'attempt': attempt,
        'feedback': feedback,
        'quiz': attempt.quiz
    }


def get_user_attempts(user_id, quiz_id=None):
    """
    Get attempt history for a user.
    
    Args:
        user_id: ID of the user
        quiz_id: Optional - filter by specific quiz
        
    Returns:
        Query object for QuizAttempt instances
    """
    query = QuizAttempt.query.filter_by(user_id=user_id)
    
    if quiz_id:
        query = query.filter_by(quiz_id=quiz_id)
    
    return query.order_by(QuizAttempt.started_at.desc())


def can_retake_quiz(user_id, quiz_id):
    """
    Check if a user is eligible to retake a quiz.
    
    Currently allows unlimited retakes. Can be extended to add restrictions.
    
    Args:
        user_id: ID of the user
        quiz_id: ID of the quiz
        
    Returns:
        tuple: (can_retake: bool, reason: str)
    """
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return False, "Quiz introuvable."
    
    # Get user's previous attempts
    previous_attempts = QuizAttempt.query.filter_by(
        user_id=user_id,
        quiz_id=quiz_id
    ).order_by(QuizAttempt.started_at.desc()).all()
    
    # Check if there are incomplete attempts
    incomplete_attempts = [a for a in previous_attempts if not a.is_completed]
    if incomplete_attempts:
        return False, "Vous avez déjà une tentative en cours."
    
    # Check if user has already passed
    passed_attempts = [a for a in previous_attempts if a.passed]
    if passed_attempts and quiz.is_eliminatory:
        # If quiz is eliminatory and user passed, they might not need to retake
        # But we'll allow it for review purposes
        pass
    
    # Allow retake (can add more rules here)
    return True, None


def get_quiz_statistics(quiz_id):
    """
    Get statistics for a quiz.
    
    Args:
        quiz_id: ID of the quiz
        
    Returns:
        dict: Statistics about the quiz attempts
    """
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return None
    
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).all()
    completed_attempts = [a for a in attempts if a.is_completed]
    passed_attempts = [a for a in completed_attempts if a.passed]
    
    if not completed_attempts:
        return {
            'total_attempts': len(attempts),
            'completed_attempts': 0,
            'pass_rate': 0,
            'average_score': 0,
            'average_time': 0
        }
    
    average_score = sum(a.score for a in completed_attempts) / len(completed_attempts)
    average_time = sum(a.time_taken for a in completed_attempts if a.time_taken) / len(completed_attempts)
    pass_rate = len(passed_attempts) / len(completed_attempts) * 100
    
    return {
        'total_attempts': len(attempts),
        'completed_attempts': len(completed_attempts),
        'passed_attempts': len(passed_attempts),
        'pass_rate': round(pass_rate, 2),
        'average_score': round(average_score, 2),
        'average_time': round(average_time, 2)
    }
