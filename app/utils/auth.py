"""
Authentication and authorization decorators and utilities.

This module provides decorators for protecting routes with authentication
and role-based access control (RBAC).
"""

import logging
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

logger = logging.getLogger(__name__)


def login_required(f):
    """
    Decorator to require authentication for a route.
    
    This is a wrapper around Flask-Login's login_required that adds
    custom messaging in French.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(roles=[]):
    """
    Decorator to require specific roles for a route.
    
    Args:
        roles: List of role names that are allowed to access the route
        
    Returns:
        Decorator function
        
    Example:
        @role_required(roles=['admin', 'manager'])
        def admin_page():
            return "Admin content"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.role or current_user.role.name not in roles:
                flash('Vous n\'avez pas les permissions nécessaires pour accéder à cette page.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(permission):
    """
    Decorator to require a specific permission for a route.
    
    Args:
        permission: Permission string to check (e.g., 'create_training')
        
    Returns:
        Decorator function
        
    Example:
        @permission_required('create_training')
        def create_training():
            return "Create training form"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not current_user.role:
                logger.error(f"User {current_user.id} has no role assigned")
                flash('Vous n\'avez pas les permissions nécessaires pour effectuer cette action.', 'danger')
                abort(403)
            
            if not has_permission(current_user, permission):
                logger.warning(f"User {current_user.id} (role: {current_user.role.name}) denied access to permission: {permission}")
                flash('Vous n\'avez pas les permissions nécessaires pour effectuer cette action.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def has_permission(user, permission):
    """
    Check if a user has a specific permission based on their role.
    
    Args:
        user: User instance to check permissions for
        permission: Permission string to check
        
    Returns:
        bool: True if user has the permission
    """
    if not user or not user.is_authenticated:
        return False
    
    if not user.role:
        return False
    
    # Check if role has the permission
    return user.role.has_permission(permission)


def check_user_permissions(user):
    """
    Get all permissions for a user based on their role.
    
    Args:
        user: User instance
        
    Returns:
        dict: Dictionary of permissions with boolean values
    """
    if not user or not user.role:
        return {}
    
    return user.role.permissions if user.role.permissions else {}
