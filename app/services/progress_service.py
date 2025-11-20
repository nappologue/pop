"""
Service for managing user training progress.

This module provides functions for tracking user progress through trainings,
including slide completion, status updates, and progress calculations.
"""

from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified
from app import db
from app.models import TrainingProgress, Training, User


def start_training(user_id, training_id):
    """
    Initialize or resume progress for a training.
    
    Args:
        user_id: ID of the user
        training_id: ID of the training
        
    Returns:
        tuple: (TrainingProgress instance, error_message)
    """
    # Check if training exists
    training = Training.query.get(training_id)
    if not training:
        return None, "Formation introuvable."
    
    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return None, "Utilisateur introuvable."
    
    # Check if progress already exists
    progress = TrainingProgress.query.filter_by(
        user_id=user_id,
        training_id=training_id
    ).first()
    
    if progress:
        # Resume existing progress
        progress.last_accessed_at = datetime.utcnow()
        db.session.commit()
        return progress, None
    
    # Create new progress
    try:
        progress = TrainingProgress(
            user_id=user_id,
            training_id=training_id,
            current_slide_index=0,
            completed_slides=[],
            quiz_attempts=[],
            status='not_started',
            started_at=datetime.utcnow(),
            last_accessed_at=datetime.utcnow()
        )
        
        db.session.add(progress)
        db.session.commit()
        
        return progress, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors du démarrage de la formation: {str(e)}"


def update_progress(user_id, training_id, slide_index):
    """
    Update current slide position for a user's training.
    
    Args:
        user_id: ID of the user
        training_id: ID of the training
        slide_index: Current slide index (0-based)
        
    Returns:
        tuple: (TrainingProgress instance, error_message)
    """
    progress = TrainingProgress.query.filter_by(
        user_id=user_id,
        training_id=training_id
    ).first()
    
    if not progress:
        return None, "Progression introuvable. Veuillez démarrer la formation."
    
    try:
        progress.current_slide_index = slide_index
        progress.last_accessed_at = datetime.utcnow()
        
        # Update status if needed
        if progress.status == 'not_started':
            progress.status = 'in_progress'
            progress.started_at = datetime.utcnow()
        
        db.session.commit()
        
        return progress, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de la mise à jour de la progression: {str(e)}"


def complete_slide(user_id, training_id, slide_index):
    """
    Mark a specific slide as completed.
    
    Args:
        user_id: ID of the user
        training_id: ID of the training
        slide_index: Index of the slide to mark as completed (0-based)
        
    Returns:
        tuple: (TrainingProgress instance, error_message)
    """
    progress = TrainingProgress.query.filter_by(
        user_id=user_id,
        training_id=training_id
    ).first()
    
    if not progress:
        return None, "Progression introuvable. Veuillez démarrer la formation."
    
    try:
        # Mark slide as completed using the model method
        progress.mark_slide_completed(slide_index)
        
        db.session.commit()
        
        return progress, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de la complétion de la diapositive: {str(e)}"


def get_user_progress(user_id, training_id):
    """
    Retrieve progress for a specific user and training.
    
    Args:
        user_id: ID of the user
        training_id: ID of the training
        
    Returns:
        TrainingProgress instance or None
    """
    return TrainingProgress.query.filter_by(
        user_id=user_id,
        training_id=training_id
    ).first()


def complete_training(user_id, training_id):
    """
    Mark a training as completed for a user.
    
    Args:
        user_id: ID of the user
        training_id: ID of the training
        
    Returns:
        tuple: (success: bool, error_message)
    """
    progress = TrainingProgress.query.filter_by(
        user_id=user_id,
        training_id=training_id
    ).first()
    
    if not progress:
        return False, "Progression introuvable."
    
    try:
        # Use the model method to mark as completed
        progress.mark_completed()
        
        db.session.commit()
        
        return True, None
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la complétion de la formation: {str(e)}"


def get_user_training_history(user_id, filters=None):
    """
    Get all training progress records for a user.
    
    Args:
        user_id: ID of the user
        filters: Optional dictionary with filters:
                - status: 'not_started', 'in_progress', 'completed'
                - training_id: specific training ID
                
    Returns:
        Query object with TrainingProgress records
    """
    query = TrainingProgress.query.filter_by(user_id=user_id)
    
    if filters:
        if 'status' in filters:
            query = query.filter_by(status=filters['status'])
        
        if 'training_id' in filters:
            query = query.filter_by(training_id=filters['training_id'])
    
    return query.order_by(TrainingProgress.last_accessed_at.desc())


def calculate_completion_percentage(progress):
    """
    Calculate the completion percentage for a training progress.
    
    Args:
        progress: TrainingProgress instance
        
    Returns:
        int: Completion percentage (0-100)
    """
    if not progress or not progress.training:
        return 0
    
    slide_count = progress.training.slide_count
    if slide_count == 0:
        return 0
    
    completed_count = len(progress.completed_slides) if progress.completed_slides else 0
    
    return int((completed_count / slide_count) * 100)
