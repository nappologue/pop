"""
Authentication routes blueprint.

This module provides routes for user authentication, registration,
and profile management.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from app import db
from app.models import User, Role, TrainingProgress
from app.services.auth_service import (
    register_user, 
    authenticate_user,
    update_user_profile,
    change_user_password,
    get_user_permissions
)
from app.utils.auth import login_required
import os

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page and handler.
    
    GET: Display login form
    POST: Process login credentials
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'
        
        # Validate input
        if not username or not password:
            flash('Veuillez entrer votre nom d\'utilisateur et votre mot de passe.', 'danger')
            return render_template('auth/login.html')
        
        # Authenticate user
        user = authenticate_user(username, password)
        
        if user:
            login_user(user, remember=remember)
            flash(f'Bienvenue, {user.full_name}!', 'success')
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
    
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    """Logout handler."""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registration page and handler.
    
    GET: Display registration form (if enabled)
    POST: Process registration
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Check if registration is enabled
    registration_enabled = os.getenv('ENABLE_REGISTRATION', 'false').lower() == 'true'
    
    if not registration_enabled:
        flash('L\'inscription n\'est pas disponible actuellement.', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        # Validate input
        errors = []
        
        if not username:
            errors.append('Le nom d\'utilisateur est requis.')
        elif len(username) < 3:
            errors.append('Le nom d\'utilisateur doit contenir au moins 3 caractères.')
        
        if not email:
            errors.append('L\'adresse email est requise.')
        
        if not password:
            errors.append('Le mot de passe est requis.')
        elif len(password) < 8:
            errors.append('Le mot de passe doit contenir au moins 8 caractères.')
        
        if password != password_confirm:
            errors.append('Les mots de passe ne correspondent pas.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html')
        
        # Get default user role
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            flash('Erreur de configuration: rôle par défaut introuvable.', 'danger')
            return render_template('auth/register.html')
        
        # Register user
        user, error = register_user({
            'username': username,
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'role_id': user_role.id
        })
        
        if error:
            flash(error, 'danger')
            return render_template('auth/register.html')
        
        # Auto-login after registration
        login_user(user)
        flash('Votre compte a été créé avec succès!', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/register.html')


@bp.route('/profile')
@login_required
def profile():
    """Display user profile page."""
    # Get user's training statistics
    total_trainings = TrainingProgress.query.filter_by(user_id=current_user.id).count()
    completed_trainings = TrainingProgress.query.filter_by(
        user_id=current_user.id, 
        status='completed'
    ).count()
    in_progress_trainings = TrainingProgress.query.filter_by(
        user_id=current_user.id,
        status='in_progress'
    ).count()
    
    # Get user permissions
    permissions = get_user_permissions(current_user)
    
    return render_template(
        'auth/profile.html',
        user=current_user,
        permissions=permissions,
        total_trainings=total_trainings,
        completed_trainings=completed_trainings,
        in_progress_trainings=in_progress_trainings
    )


@bp.route('/profile/update', methods=['POST'])
@login_required
def profile_update():
    """Update user profile information."""
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    team = request.form.get('team', '').strip()
    location = request.form.get('location', '').strip()
    
    # Validate email
    if not email:
        flash('L\'adresse email est requise.', 'danger')
        return redirect(url_for('auth.profile'))
    
    # Update profile
    success, error = update_user_profile(current_user, {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'team': team if team else None,
        'location': location if location else None
    })
    
    if success:
        flash('Votre profil a été mis à jour avec succès.', 'success')
    else:
        flash(error, 'danger')
    
    return redirect(url_for('auth.profile'))


@bp.route('/profile/password', methods=['POST'])
@login_required
def profile_password():
    """Change user password."""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    new_password_confirm = request.form.get('new_password_confirm', '')
    
    # Validate input
    if not current_password or not new_password or not new_password_confirm:
        flash('Tous les champs sont requis.', 'danger')
        return redirect(url_for('auth.profile'))
    
    if new_password != new_password_confirm:
        flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
        return redirect(url_for('auth.profile'))
    
    # Change password
    success, error = change_user_password(current_user, current_password, new_password)
    
    if success:
        flash('Votre mot de passe a été changé avec succès.', 'success')
    else:
        flash(error, 'danger')
    
    return redirect(url_for('auth.profile'))
