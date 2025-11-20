"""
Database initialization utilities.

This module provides functions to initialize the database with default
roles, permissions, and admin user.
"""

import os
from app import db
from app.models import Role, User


def create_default_roles():
    """
    Create default roles with their permissions.
    
    Creates three roles:
    - admin: Full access to all features
    - manager: Can manage trainings and view team statistics
    - user: Basic access to view and take trainings
    
    Returns:
        tuple: (admin_role, manager_role, user_role)
    """
    # Admin role - all permissions
    admin_permissions = {
        'view_dashboard': True,
        'view_trainings': True,
        'create_training': True,
        'edit_training': True,
        'delete_training': True,
        'publish_training': True,
        'view_all_trainings': True,
        'manage_trainings': True,
        'create_quiz': True,
        'edit_quiz': True,
        'delete_quiz': True,
        'manage_quizzes': True,
        'view_users': True,
        'create_user': True,
        'edit_user': True,
        'delete_user': True,
        'view_roles': True,
        'manage_roles': True,
        'view_all_stats': True,
        'view_team_stats': True,
        'export_data': True,
        'manage_settings': True
    }
    
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(
            name='admin',
            permissions=admin_permissions
        )
        db.session.add(admin_role)
        print("✓ Created admin role")
    else:
        admin_role.permissions = admin_permissions
        print("✓ Updated admin role permissions")
    
    # Manager role - manage trainings and view team stats
    manager_role = Role.query.filter_by(name='manager').first()
    if not manager_role:
        manager_role = Role(
            name='manager',
            permissions={
                'view_dashboard': True,
                'view_trainings': True,
                'create_training': True,
                'edit_training': True,
                'publish_training': True,
                'view_all_trainings': True,
                'create_quiz': True,
                'edit_quiz': True,
                'view_team_stats': True,
                'export_data': True
            }
        )
        db.session.add(manager_role)
        print("✓ Created manager role")
    else:
        print("- Manager role already exists")
    
    # User role - basic access
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        user_role = Role(
            name='user',
            permissions={
                'view_dashboard': True,
                'view_trainings': True,
                'take_training': True,
                'take_quiz': True,
                'view_own_stats': True
            }
        )
        db.session.add(user_role)
        print("✓ Created user role")
    else:
        print("- User role already exists")
    
    # Commit all roles
    try:
        db.session.commit()
        print("✓ All roles committed to database")
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error committing roles: {e}")
        raise
    
    return admin_role, manager_role, user_role


def create_default_admin():
    """
    Create default admin user from environment variables.
    
    Reads admin credentials from .env file:
    - ADMIN_USERNAME (default: admin)
    - ADMIN_EMAIL (default: admin@localhost)
    - ADMIN_PASSWORD (default: admin123)
    - ADMIN_FIRST_NAME (optional)
    - ADMIN_LAST_NAME (optional)
    
    Returns:
        User: Admin user instance
    """
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@localhost')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    admin_first_name = os.getenv('ADMIN_FIRST_NAME', 'Admin')
    admin_last_name = os.getenv('ADMIN_LAST_NAME', 'User')
    
    # Check if admin already exists
    existing_admin = User.query.filter_by(username=admin_username).first()
    if existing_admin:
        print(f"- Admin user '{admin_username}' already exists")
        return existing_admin
    
    # Get admin role
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        raise Exception("Admin role must be created before creating admin user")
    
    # Create admin user
    admin_user = User(
        username=admin_username,
        email=admin_email,
        first_name=admin_first_name,
        last_name=admin_last_name,
        role_id=admin_role.id,
        is_active=True
    )
    admin_user.set_password(admin_password)
    
    db.session.add(admin_user)
    
    try:
        db.session.commit()
        print(f"✓ Created admin user: {admin_username}")
        print(f"  Email: {admin_email}")
        print(f"  Password: {'*' * len(admin_password)}")
        return admin_user
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error creating admin user: {e}")
        raise


def initialize_database():
    """
    Initialize database with default roles and admin user.
    
    This function should be called once when setting up the application
    for the first time. It's safe to call multiple times as it checks
    for existing data before creating.
    
    Returns:
        bool: True if initialization successful
    """
    print("\n" + "="*50)
    print("Initializing Database")
    print("="*50 + "\n")
    
    try:
        # Create default roles
        print("Creating default roles...")
        create_default_roles()
        print()
        
        # Create default admin user
        print("Creating default admin user...")
        create_default_admin()
        print()
        
        print("="*50)
        print("Database initialization complete!")
        print("="*50 + "\n")
        
        return True
        
    except Exception as e:
        print("\n" + "="*50)
        print(f"Database initialization failed: {e}")
        print("="*50 + "\n")
        return False


def check_initialization_needed():
    """
    Check if database initialization is needed.
    
    Returns:
        bool: True if initialization is needed (no roles exist)
    """
    role_count = Role.query.count()
    return role_count == 0
