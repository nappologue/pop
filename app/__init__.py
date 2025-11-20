"""
Flask application factory for POP (Plateforme d'Optimisation des Progressions).

This module initializes the Flask application with all necessary extensions
and configurations for the continuous learning platform.
"""

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config=None):
    """
    Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary to override defaults
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__, template_folder='../templates')
    
    # Load configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://pop_user:password@localhost:5432/pop_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['APP_NAME'] = os.getenv('APP_NAME', 'POP - Plateforme d\'Optimisation des Progressions')
    app.config['ITEMS_PER_PAGE'] = int(os.getenv('ITEMS_PER_PAGE', 20))
    
    # Session security
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('MODE', 'DEV') == 'PROD'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Override with custom config if provided
    if config:
        app.config.update(config)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login."""
        from app.models import User
        return User.query.get(int(user_id))
    
    # Before request handler for RBAC and session management
    @app.before_request
    def before_request():
        """
        Execute before each request.
        
        Updates last_accessed_at for active users and can enforce RBAC rules.
        """
        from flask_login import current_user
        from datetime import datetime
        
        if current_user.is_authenticated:
            # Check if user is active
            if not current_user.is_active:
                from flask_login import logout_user
                from flask import flash, redirect, url_for
                logout_user()
                flash('Votre compte a été désactivé. Veuillez contacter un administrateur.', 'error')
                return redirect(url_for('auth.login'))
    
    # Register blueprints
    from app.routes import auth
    app.register_blueprint(auth.bp)
    
    from app.routes import training
    app.register_blueprint(training.bp)
    
    from app.routes import quiz
    app.register_blueprint(quiz.bp)
    
    from app.routes.admin import training as admin_training
    app.register_blueprint(admin_training.bp)
    
    from app.routes.admin import quiz as admin_quiz
    app.register_blueprint(admin_quiz.bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_app_config():
        """Inject common variables into all templates."""
        return {
            'app_name': app.config['APP_NAME'],
            'mode': os.getenv('MODE', 'DEV')
        }
    
    # Home route
    @app.route('/')
    def index():
        """Home page route."""
        return render_template('base.html')
    
    return app


# Create application instance for Gunicorn
app = create_app()
