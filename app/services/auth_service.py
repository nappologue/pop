"""
Authentication service for user management and authentication.

This module provides functions for user registration, authentication,
and permission management.
"""

from datetime import datetime
from app import db
from app.models import User, Role


def register_user(data):
    """
    Register a new user with hashed password.
    
    Args:
        data: Dictionary containing user registration data
              Required keys: username, email, password, role_id
              Optional keys: first_name, last_name, team, location, anciennete
              
    Returns:
        tuple: (User instance, error_message)
               User instance if successful, None if error
               error_message is None if successful, error string if error
               
    Example:
        user, error = register_user({
            'username': 'jdoe',
            'email': 'jdoe@example.com',
            'password': 'securepass123',
            'role_id': 3,
            'first_name': 'John',
            'last_name': 'Doe'
        })
    """
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'role_id']
    for field in required_fields:
        if field not in data or not data[field]:
            return None, f"Le champ {field} est requis."
    
    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return None, "Ce nom d'utilisateur est déjà utilisé."
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return None, "Cette adresse email est déjà utilisée."
    
    # Check if role exists
    role = Role.query.get(data['role_id'])
    if not role:
        return None, "Le rôle spécifié n'existe pas."
    
    try:
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            role_id=data['role_id'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            team=data.get('team'),
            location=data.get('location'),
            anciennete=data.get('anciennete'),
            is_active=True
        )
        
        # Hash and set password
        user.set_password(data['password'])
        
        # Add to database
        db.session.add(user)
        db.session.commit()
        
        return user, None
        
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de la création de l'utilisateur: {str(e)}"


def authenticate_user(username, password):
    """
    Authenticate a user with username and password.
    
    Args:
        username: Username or email
        password: Plain text password
        
    Returns:
        User instance if authentication successful, None otherwise
    """
    # Try to find user by username or email
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    # Check if user exists and password is correct
    if user and user.check_password(password):
        # Check if user is active
        if not user.is_active:
            return None
        return user
    
    return None


def get_user_permissions(user):
    """
    Get all permissions for a user based on their role.
    
    Args:
        user: User instance
        
    Returns:
        dict: Dictionary of permissions with boolean values
        
    Example:
        permissions = get_user_permissions(user)
        # Returns: {'create_training': True, 'view_stats': True, ...}
    """
    if not user or not user.role:
        return {}
    
    return user.role.permissions if user.role.permissions else {}


def check_permission(user, permission):
    """
    Check if a user has a specific permission.
    
    Args:
        user: User instance
        permission: Permission string to check (e.g., 'create_training')
        
    Returns:
        bool: True if user has the permission
    """
    if not user or not user.is_authenticated:
        return False
    
    if not user.role:
        return False
    
    return user.role.has_permission(permission)


def update_user_profile(user, data):
    """
    Update user profile information.
    
    Args:
        user: User instance to update
        data: Dictionary containing fields to update
              Allowed keys: first_name, last_name, email, team, location, anciennete
              
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    allowed_fields = ['first_name', 'last_name', 'email', 'team', 'location', 'anciennete']
    
    try:
        # Check if email is being changed and if it's already in use
        if 'email' in data and data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return False, "Cette adresse email est déjà utilisée."
        
        # Update allowed fields
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, None
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la mise à jour du profil: {str(e)}"


def change_user_password(user, current_password, new_password):
    """
    Change a user's password.
    
    Args:
        user: User instance
        current_password: Current password for verification
        new_password: New password to set
        
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    # Verify current password
    if not user.check_password(current_password):
        return False, "Le mot de passe actuel est incorrect."
    
    # Validate new password
    if len(new_password) < 8:
        return False, "Le nouveau mot de passe doit contenir au moins 8 caractères."
    
    try:
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, None
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors du changement de mot de passe: {str(e)}"
