"""
Admin dashboard routes for statistics and overview.

This module provides routes for the admin dashboard with statistics and charts.
"""

from flask import Blueprint, render_template, jsonify
from flask_login import current_user
from app.utils.auth import login_required, permission_required
from app import db
from app.models import Training, Quiz, User, TrainingProgress, QuizAttempt
from sqlalchemy import func, case
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@bp.route('/dashboard')
@login_required
@permission_required('view_dashboard')
def dashboard():
    """
    Admin dashboard with statistics and overview.
    
    GET /admin/dashboard
    """
    # Get statistics
    stats = get_dashboard_statistics()
    
    return render_template('admin/dashboard.html', stats=stats)


@bp.route('/statistics')
@login_required
@permission_required('view_all_stats')
def statistics():
    """
    Detailed statistics page.
    
    GET /admin/statistics
    """
    return render_template('admin/statistics.html')


@bp.route('/api/statistics/overview')
@login_required
@permission_required('view_all_stats')
def statistics_overview():
    """
    Get overview statistics (AJAX).
    
    GET /admin/api/statistics/overview
    """
    stats = get_dashboard_statistics()
    return jsonify(stats)


@bp.route('/api/statistics/completions')
@login_required
@permission_required('view_all_stats')
def statistics_completions():
    """
    Get completion statistics over time (AJAX).
    
    GET /admin/api/statistics/completions
    """
    # Get completions over the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    completions = db.session.query(
        func.date(TrainingProgress.completed_at).label('date'),
        func.count(TrainingProgress.id).label('count')
    ).filter(
        TrainingProgress.completed_at >= thirty_days_ago,
        TrainingProgress.status == 'completed'
    ).group_by(
        func.date(TrainingProgress.completed_at)
    ).order_by('date').all()
    
    return jsonify({
        'labels': [str(c.date) for c in completions],
        'data': [c.count for c in completions]
    })


@bp.route('/api/statistics/scores')
@login_required
@permission_required('view_all_stats')
def statistics_scores():
    """
    Get score distribution (AJAX).
    
    GET /admin/api/statistics/scores
    """
    # Get all completed quiz attempts
    attempts = QuizAttempt.query.filter_by(is_completed=True).all()
    
    # Distribute scores into bins
    bins = {
        '0-20%': 0,
        '21-40%': 0,
        '41-60%': 0,
        '61-80%': 0,
        '81-100%': 0
    }
    
    for attempt in attempts:
        score = attempt.score
        if score <= 20:
            bins['0-20%'] += 1
        elif score <= 40:
            bins['21-40%'] += 1
        elif score <= 60:
            bins['41-60%'] += 1
        elif score <= 80:
            bins['61-80%'] += 1
        else:
            bins['81-100%'] += 1
    
    return jsonify({
        'labels': list(bins.keys()),
        'data': list(bins.values())
    })


@bp.route('/api/statistics/users')
@login_required
@permission_required('view_all_stats')
def statistics_users():
    """
    Get user statistics data (AJAX).
    
    GET /admin/api/statistics/users
    """
    # Get all users with their statistics
    users = User.query.filter_by(is_active=True).all()
    
    user_stats = []
    for user in users:
        # Get training progress
        completed_trainings = TrainingProgress.query.filter_by(
            user_id=user.id,
            status='completed'
        ).count()
        
        # Get average quiz score
        quiz_attempts = QuizAttempt.query.filter_by(
            user_id=user.id,
            is_completed=True
        ).all()
        
        avg_score = 0
        if quiz_attempts:
            avg_score = sum(a.score for a in quiz_attempts) / len(quiz_attempts)
        
        # Get last activity
        last_progress = TrainingProgress.query.filter_by(
            user_id=user.id
        ).order_by(TrainingProgress.updated_at.desc()).first()
        
        last_activity = None
        if last_progress:
            last_activity = last_progress.updated_at.strftime('%Y-%m-%d')
        
        user_stats.append({
            'name': user.full_name or user.username,
            'email': user.email,
            'team': user.team or 'N/A',
            'location': user.location or 'N/A',
            'anciennete': user.anciennete or 'N/A',
            'completed_trainings': completed_trainings,
            'average_score': round(avg_score, 1),
            'last_activity': last_activity or 'N/A'
        })
    
    return jsonify({'data': user_stats})


def get_dashboard_statistics():
    """
    Calculate dashboard statistics.
    
    Returns:
        dict: Dashboard statistics
    """
    # Total counts
    total_users = User.query.filter_by(is_active=True).count()
    total_trainings = Training.query.filter_by(is_published=True).count()
    total_quizzes = Quiz.query.count()
    
    # This month's completions
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    completions_this_month = TrainingProgress.query.filter(
        TrainingProgress.completed_at >= start_of_month,
        TrainingProgress.status == 'completed'
    ).count()
    
    # Calculate completion rate this month
    active_progress = TrainingProgress.query.filter(
        TrainingProgress.updated_at >= start_of_month
    ).count()
    
    completion_rate = 0
    if active_progress > 0:
        completion_rate = (completions_this_month / active_progress) * 100
    
    # Average quiz scores
    completed_attempts = QuizAttempt.query.filter_by(is_completed=True).all()
    avg_quiz_score = 0
    if completed_attempts:
        avg_quiz_score = sum(a.score for a in completed_attempts) / len(completed_attempts)
    
    # Recent activity (last 10 completions)
    recent_activity = TrainingProgress.query.filter_by(
        status='completed'
    ).order_by(
        TrainingProgress.completed_at.desc()
    ).limit(10).all()
    
    return {
        'total_users': total_users,
        'total_trainings': total_trainings,
        'total_quizzes': total_quizzes,
        'completions_this_month': completions_this_month,
        'completion_rate': round(completion_rate, 1),
        'avg_quiz_score': round(avg_quiz_score, 1),
        'recent_activity': recent_activity
    }
