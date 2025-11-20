"""
Service for managing training content.

This module provides functions for creating, updating, retrieving, and managing
training content, including publishing and assignment workflows.
"""

from datetime import datetime
from sqlalchemy import or_, and_
from app import db
from app.models import Training, User


def create_training(data, creator_id):
    """
    Create a new training.
    
    Args:
        data: Dictionary containing training data
              Required: title, slides
              Optional: description, is_mandatory, target_roles, target_teams, target_locations
        creator_id: ID of the user creating the training
        
    Returns:
        tuple: (Training instance, error_message)
               Training instance if successful, None if error
               error_message is None if successful, error string if error
    """
    # Validate required fields
    if not data.get('title'):
        return None, "Le titre est requis."
    
    if not data.get('slides') or not isinstance(data.get('slides'), list):
        return None, "Les diapositives sont requises et doivent être une liste."
    
    if len(data.get('slides', [])) == 0:
        return None, "Au moins une diapositive est requise."
    
    try:
        training = Training(
            title=data['title'],
            description=data.get('description', ''),
            created_by=creator_id,
            slides=data['slides'],
            is_published=False,
            is_mandatory=data.get('is_mandatory', False),
            target_roles=data.get('target_roles', []),
            target_teams=data.get('target_teams', []),
            target_locations=data.get('target_locations', [])
        )
        
        db.session.add(training)
        db.session.commit()
        
        return training, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de la création de la formation: {str(e)}"


def update_training(training_id, data):
    """
    Update an existing training.
    
    Args:
        training_id: ID of the training to update
        data: Dictionary containing fields to update
              Allowed: title, description, slides, is_mandatory, target_roles, 
                       target_teams, target_locations
        
    Returns:
        tuple: (Training instance, error_message)
    """
    training = Training.query.get(training_id)
    
    if not training:
        return None, "Formation introuvable."
    
    # Don't allow updating published trainings
    if training.is_published and 'slides' in data:
        return None, "Impossible de modifier les diapositives d'une formation publiée. Veuillez la dépublier d'abord."
    
    allowed_fields = [
        'title', 'description', 'slides', 'is_mandatory',
        'target_roles', 'target_teams', 'target_locations'
    ]
    
    try:
        for field in allowed_fields:
            if field in data:
                setattr(training, field, data[field])
        
        training.updated_at = datetime.utcnow()
        db.session.commit()
        
        return training, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de la mise à jour de la formation: {str(e)}"


def delete_training(training_id):
    """
    Soft delete a training.
    
    Args:
        training_id: ID of the training to delete
        
    Returns:
        tuple: (success: bool, error_message)
    """
    training = Training.query.get(training_id)
    
    if not training:
        return False, "Formation introuvable."
    
    try:
        # Unpublish before deletion
        training.is_published = False
        db.session.commit()
        
        return True, None
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la suppression de la formation: {str(e)}"


def get_training_by_id(training_id):
    """
    Retrieve a single training by ID.
    
    Args:
        training_id: ID of the training
        
    Returns:
        Training instance or None
    """
    return Training.query.get(training_id)


def get_trainings_for_user(user_id):
    """
    Get all published trainings assigned to a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        list: List of Training instances targeted to this user
    """
    user = User.query.get(user_id)
    
    if not user:
        return []
    
    # Get all published trainings
    all_trainings = Training.query.filter_by(is_published=True).all()
    
    # Filter trainings targeted to this user
    user_trainings = [
        training for training in all_trainings
        if training.is_targeted_to_user(user)
    ]
    
    return user_trainings


def get_all_trainings(filters=None):
    """
    Get all trainings with optional filters (admin view).
    
    Args:
        filters: Dictionary with optional filter criteria
                 - is_published (bool)
                 - is_mandatory (bool)
                 - created_by (int)
                 - search (str): search in title/description
                 - target_role (str)
                 - target_team (str)
                 - target_location (str)
        
    Returns:
        Query object that can be paginated
    """
    query = Training.query
    
    if filters:
        if 'is_published' in filters:
            query = query.filter_by(is_published=filters['is_published'])
        
        if 'is_mandatory' in filters:
            query = query.filter_by(is_mandatory=filters['is_mandatory'])
        
        if 'created_by' in filters:
            query = query.filter_by(created_by=filters['created_by'])
        
        if 'search' in filters and filters['search']:
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Training.title.ilike(search_term),
                    Training.description.ilike(search_term)
                )
            )
        
        if 'target_role' in filters and filters['target_role']:
            # Filter trainings that include this role in target_roles
            query = query.filter(
                Training.target_roles.contains([filters['target_role']])
            )
        
        if 'target_team' in filters and filters['target_team']:
            query = query.filter(
                Training.target_teams.contains([filters['target_team']])
            )
        
        if 'target_location' in filters and filters['target_location']:
            query = query.filter(
                Training.target_locations.contains([filters['target_location']])
            )
    
    return query.order_by(Training.created_at.desc())


def publish_training(training_id):
    """
    Mark a training as published.
    
    Args:
        training_id: ID of the training to publish
        
    Returns:
        tuple: (success: bool, error_message)
    """
    training = Training.query.get(training_id)
    
    if not training:
        return False, "Formation introuvable."
    
    # Validate training has content
    if not training.slides or len(training.slides) == 0:
        return False, "Impossible de publier une formation sans diapositives."
    
    try:
        training.is_published = True
        training.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, None
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la publication de la formation: {str(e)}"


def assign_training_to_users(training_id, user_criteria):
    """
    Bulk assign training to users based on criteria.
    
    This function updates the targeting options of a training to automatically
    assign it to users matching the criteria.
    
    Args:
        training_id: ID of the training
        user_criteria: Dictionary with criteria:
                      - roles: list of role names
                      - teams: list of team names
                      - locations: list of location names
        
    Returns:
        tuple: (success: bool, error_message)
    """
    training = Training.query.get(training_id)
    
    if not training:
        return False, "Formation introuvable."
    
    try:
        # Update targeting options
        if 'roles' in user_criteria and user_criteria['roles']:
            training.target_roles = user_criteria['roles']
        
        if 'teams' in user_criteria and user_criteria['teams']:
            training.target_teams = user_criteria['teams']
        
        if 'locations' in user_criteria and user_criteria['locations']:
            training.target_locations = user_criteria['locations']
        
        training.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, None
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de l'affectation de la formation: {str(e)}"
