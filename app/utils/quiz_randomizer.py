"""
Quiz randomization utilities.

This module provides functions for randomizing quiz questions and answers,
generating unique identifiers, and validating quiz integrity.
"""

import random
import hashlib
import json


def randomize_question_selection(quiz, pool_size=None):
    """
    Randomly select N questions from quiz question pool.
    
    Args:
        quiz: Quiz model instance
        pool_size: Number of questions to select (None = all questions)
        
    Returns:
        list: List of selected Question instances
    """
    all_questions = quiz.questions.all()
    
    # If pool_size is not specified or greater than available, return all
    if pool_size is None or pool_size >= len(all_questions):
        return all_questions
    
    # Randomly select pool_size questions
    return random.sample(all_questions, min(pool_size, len(all_questions)))


def randomize_answer_order(question):
    """
    Shuffle answer order for a question while tracking correct positions.
    
    Args:
        question: Question model instance
        
    Returns:
        dict: {
            'question_id': int,
            'shuffled_answers': list of answer dicts with shuffled order,
            'answer_mapping': dict mapping new index -> original index
        }
    """
    if not question.answers:
        return {
            'question_id': question.id,
            'shuffled_answers': [],
            'answer_mapping': {}
        }
    
    # Create list of (original_index, answer) tuples
    indexed_answers = list(enumerate(question.answers))
    
    # Shuffle the list
    random.shuffle(indexed_answers)
    
    # Build mapping and shuffled answers
    answer_mapping = {}
    shuffled_answers = []
    
    for new_index, (original_index, answer) in enumerate(indexed_answers):
        answer_mapping[new_index] = original_index
        shuffled_answers.append(answer)
    
    return {
        'question_id': question.id,
        'shuffled_answers': shuffled_answers,
        'answer_mapping': answer_mapping
    }


def generate_quiz_hash(quiz_instance):
    """
    Generate a unique hash for a quiz instance for validation.
    
    The hash is based on quiz_id, selected question IDs, and answer mappings.
    
    Args:
        quiz_instance: Dictionary containing:
            - quiz_id: int
            - questions: list of question data with mappings
            
    Returns:
        str: SHA256 hash of the quiz instance
    """
    # Create a deterministic string representation
    instance_data = {
        'quiz_id': quiz_instance.get('quiz_id'),
        'question_ids': [q.get('question_id') for q in quiz_instance.get('questions', [])],
        'mappings': [q.get('answer_mapping') for q in quiz_instance.get('questions', [])]
    }
    
    # Convert to JSON string (sorted keys for determinism)
    instance_str = json.dumps(instance_data, sort_keys=True)
    
    # Generate SHA256 hash
    return hashlib.sha256(instance_str.encode()).hexdigest()


def validate_quiz_integrity(attempt, quiz_hash):
    """
    Validate that quiz attempt matches the generated instance hash.
    
    This prevents tampering with quiz instances during the attempt.
    
    Args:
        attempt: QuizAttempt model instance
        quiz_hash: Expected hash string
        
    Returns:
        bool: True if valid, False if tampered
    """
    if not attempt or not quiz_hash:
        return False
    
    # Get quiz instance data from attempt
    quiz_instance = attempt.answers_given.get('_quiz_instance')
    
    if not quiz_instance:
        # If no instance data stored, cannot validate (legacy attempts)
        return True
    
    # Regenerate hash from stored instance data
    regenerated_hash = generate_quiz_hash(quiz_instance)
    
    # Compare hashes
    return regenerated_hash == quiz_hash
