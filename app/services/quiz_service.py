"""
Service for managing quiz content.

This module provides functions for creating, updating, retrieving, and managing
quizzes and their questions.
"""

from datetime import datetime
from app import db
from app.models import Quiz, Question
from app.utils.quiz_randomizer import randomize_question_selection, randomize_answer_order, generate_quiz_hash


def create_quiz(data):
    """
    Create a new quiz.
    
    Args:
        data: Dictionary containing quiz data
              Required: title
              Optional: description, training_id, question_pool_size, minimum_score,
                       time_limit, is_eliminatory, position_in_training, randomize_answers
              
    Returns:
        tuple: (Quiz instance, error_message)
               Quiz instance if successful, None if error
               error_message is None if successful, error string if error
    """
    # Validate required fields
    if not data.get('title'):
        return None, "Le titre est requis."
    
    try:
        quiz = Quiz(
            title=data['title'],
            description=data.get('description', ''),
            training_id=data.get('training_id'),
            question_pool_size=data.get('question_pool_size'),
            minimum_score=data.get('minimum_score', 70),
            time_limit=data.get('time_limit'),
            is_eliminatory=data.get('is_eliminatory', False),
            position_in_training=data.get('position_in_training'),
            randomize_answers=data.get('randomize_answers', True)
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        return quiz, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de la création du quiz: {str(e)}"


def update_quiz(quiz_id, data):
    """
    Update an existing quiz.
    
    Args:
        quiz_id: ID of the quiz to update
        data: Dictionary containing fields to update
              Allowed: title, description, question_pool_size, minimum_score,
                       time_limit, is_eliminatory, position_in_training, randomize_answers
              
    Returns:
        tuple: (Quiz instance, error_message)
    """
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return None, "Quiz introuvable."
    
    allowed_fields = [
        'title', 'description', 'question_pool_size', 'minimum_score',
        'time_limit', 'is_eliminatory', 'position_in_training', 'randomize_answers'
    ]
    
    try:
        for field in allowed_fields:
            if field in data:
                setattr(quiz, field, data[field])
        
        quiz.updated_at = datetime.utcnow()
        db.session.commit()
        
        return quiz, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de la mise à jour du quiz: {str(e)}"


def delete_quiz(quiz_id):
    """
    Delete a quiz and all its questions.
    
    Args:
        quiz_id: ID of the quiz to delete
        
    Returns:
        tuple: (success: bool, error_message)
    """
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return False, "Quiz introuvable."
    
    try:
        # Delete quiz (cascade will delete questions and attempts)
        db.session.delete(quiz)
        db.session.commit()
        
        return True, None
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la suppression du quiz: {str(e)}"


def get_quiz_by_id(quiz_id):
    """
    Retrieve a single quiz by ID.
    
    Args:
        quiz_id: ID of the quiz
        
    Returns:
        Quiz instance or None
    """
    return Quiz.query.get(quiz_id)


def generate_quiz_instance(quiz_id):
    """
    Generate a randomized quiz instance for a new attempt.
    
    This selects questions (if pool_size is set) and randomizes answer order.
    
    Args:
        quiz_id: ID of the quiz
        
    Returns:
        dict: {
            'quiz_id': int,
            'questions': list of question data with randomized answers,
            'quiz_hash': str - unique hash for validation
        }
        or None if error
    """
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return None
    
    # Select questions (random if pool_size is set)
    selected_questions = randomize_question_selection(quiz, quiz.question_pool_size)
    
    if not selected_questions:
        return None
    
    # Build quiz instance
    questions_data = []
    question_ids = []
    
    for question in selected_questions:
        question_data = {
            'question_id': question.id,
            'question_text': question.question_text,
            'question_type': question.question_type,
            'points': question.points,
            'order_index': question.order_index
        }
        
        # Randomize answers if enabled
        if quiz.randomize_answers:
            randomized = randomize_answer_order(question)
            question_data['answers'] = randomized['shuffled_answers']
            question_data['answer_mapping'] = randomized['answer_mapping']
        else:
            question_data['answers'] = question.answers
            question_data['answer_mapping'] = {i: i for i in range(len(question.answers))}
        
        questions_data.append(question_data)
        question_ids.append(question.id)
    
    # Build quiz instance dictionary
    quiz_instance = {
        'quiz_id': quiz_id,
        'questions': questions_data,
        'question_ids': question_ids
    }
    
    # Generate hash for integrity validation
    quiz_hash = generate_quiz_hash(quiz_instance)
    quiz_instance['quiz_hash'] = quiz_hash
    
    return quiz_instance


def get_quizzes_for_training(training_id):
    """
    Get all quizzes associated with a training.
    
    Args:
        training_id: ID of the training
        
    Returns:
        list: List of Quiz instances
    """
    return Quiz.query.filter_by(training_id=training_id).order_by(
        Quiz.position_in_training.asc().nullslast(),
        Quiz.created_at.asc()
    ).all()


def get_all_quizzes(filters=None):
    """
    Get all quizzes with optional filters (admin view).
    
    Args:
        filters: Dictionary with optional filter criteria
                 - training_id (int): filter by training
                 - is_eliminatory (bool)
                 - search (str): search in title/description
                 
    Returns:
        Query object that can be paginated
    """
    query = Quiz.query
    
    if filters:
        if 'training_id' in filters:
            if filters['training_id'] is None:
                # Standalone quizzes
                query = query.filter(Quiz.training_id.is_(None))
            else:
                query = query.filter_by(training_id=filters['training_id'])
        
        if 'is_eliminatory' in filters:
            query = query.filter_by(is_eliminatory=filters['is_eliminatory'])
        
        if 'search' in filters and filters['search']:
            search_term = f"%{filters['search']}%"
            query = query.filter(
                db.or_(
                    Quiz.title.ilike(search_term),
                    Quiz.description.ilike(search_term)
                )
            )
    
    return query.order_by(Quiz.created_at.desc())


def add_question_to_quiz(quiz_id, question_data):
    """
    Add a new question to a quiz.
    
    Args:
        quiz_id: ID of the quiz
        question_data: Dictionary with question data
                      Required: question_text, question_type, answers
                      Optional: points, order_index
                      
    Returns:
        tuple: (Question instance, error_message)
    """
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return None, "Quiz introuvable."
    
    # Validate required fields
    if not question_data.get('question_text'):
        return None, "Le texte de la question est requis."
    
    if not question_data.get('question_type'):
        return None, "Le type de question est requis."
    
    if not question_data.get('answers') or not isinstance(question_data.get('answers'), list):
        return None, "Les réponses sont requises."
    
    try:
        # Get next order_index if not provided
        order_index = question_data.get('order_index')
        if order_index is None:
            max_order = db.session.query(db.func.max(Question.order_index)).filter_by(quiz_id=quiz_id).scalar()
            order_index = (max_order or 0) + 1
        
        question = Question(
            quiz_id=quiz_id,
            question_text=question_data['question_text'],
            question_type=question_data['question_type'],
            answers=question_data['answers'],
            points=question_data.get('points', 1),
            order_index=order_index
        )
        
        db.session.add(question)
        db.session.commit()
        
        return question, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de l'ajout de la question: {str(e)}"


def update_question(question_id, question_data):
    """
    Update an existing question.
    
    Args:
        question_id: ID of the question to update
        question_data: Dictionary with fields to update
                      
    Returns:
        tuple: (Question instance, error_message)
    """
    question = Question.query.get(question_id)
    
    if not question:
        return None, "Question introuvable."
    
    allowed_fields = ['question_text', 'question_type', 'answers', 'points', 'order_index']
    
    try:
        for field in allowed_fields:
            if field in question_data:
                setattr(question, field, question_data[field])
        
        db.session.commit()
        
        return question, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de la mise à jour de la question: {str(e)}"


def delete_question(question_id):
    """
    Delete a question from a quiz.
    
    Args:
        question_id: ID of the question to delete
        
    Returns:
        tuple: (success: bool, error_message)
    """
    question = Question.query.get(question_id)
    
    if not question:
        return False, "Question introuvable."
    
    try:
        db.session.delete(question)
        db.session.commit()
        
        return True, None
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la suppression de la question: {str(e)}"
