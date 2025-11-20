"""
Training routes blueprint for user-facing training functionality.

This module provides routes for users to view, start, and complete trainings.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user
from app.utils.auth import login_required
from app.services import training_service, progress_service
from app.utils.slide_handlers import render_slide, validate_slide_completion

bp = Blueprint('training', __name__, url_prefix='/trainings')


@bp.route('/')
@login_required
def list_trainings():
    """
    List all trainings assigned to the current user.
    
    GET /trainings
    """
    # Get trainings for current user
    trainings = training_service.get_trainings_for_user(current_user.id)
    
    # Get progress for each training
    training_data = []
    for training in trainings:
        progress = progress_service.get_user_progress(current_user.id, training.id)
        
        training_info = {
            'training': training,
            'progress': progress,
            'completion_percentage': progress.completion_percentage if progress else 0,
            'status': progress.status if progress else 'not_started'
        }
        training_data.append(training_info)
    
    return render_template('training/list.html', training_data=training_data)


@bp.route('/<int:training_id>')
@login_required
def view_training(training_id):
    """
    View a specific training (slideshow player).
    
    GET /trainings/<id>
    """
    training = training_service.get_training_by_id(training_id)
    
    if not training:
        flash('Formation introuvable.', 'danger')
        return redirect(url_for('training.list_trainings'))
    
    # Check if training is published
    if not training.is_published:
        flash('Cette formation n\'est pas encore disponible.', 'warning')
        return redirect(url_for('training.list_trainings'))
    
    # Check if user has access
    if not training.is_targeted_to_user(current_user):
        flash('Vous n\'avez pas accès à cette formation.', 'danger')
        return redirect(url_for('training.list_trainings'))
    
    # Get or create progress
    progress = progress_service.get_user_progress(current_user.id, training_id)
    if not progress:
        progress, error = progress_service.start_training(current_user.id, training_id)
        if error:
            flash(error, 'danger')
            return redirect(url_for('training.list_trainings'))
    
    return render_template(
        'training/view.html',
        training=training,
        progress=progress
    )


@bp.route('/<int:training_id>/start', methods=['POST'])
@login_required
def start_training(training_id):
    """
    Start or resume a training.
    
    POST /trainings/<id>/start
    """
    training = training_service.get_training_by_id(training_id)
    
    if not training or not training.is_published:
        return jsonify({'error': 'Formation introuvable'}), 404
    
    if not training.is_targeted_to_user(current_user):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    progress, error = progress_service.start_training(current_user.id, training_id)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'success': True,
        'progress': {
            'current_slide_index': progress.current_slide_index,
            'completed_slides': progress.completed_slides,
            'status': progress.status,
            'completion_percentage': progress.completion_percentage
        }
    })


@bp.route('/<int:training_id>/progress', methods=['POST'])
@login_required
def update_progress(training_id):
    """
    Update progress for a training (AJAX).
    
    POST /trainings/<id>/progress
    Body: { "slide_index": 2 }
    """
    data = request.get_json()
    
    if not data or 'slide_index' not in data:
        return jsonify({'error': 'Index de diapositive requis'}), 400
    
    slide_index = data['slide_index']
    
    # Validate slide_index
    if not isinstance(slide_index, int) or slide_index < 0:
        return jsonify({'error': 'Index de diapositive invalide'}), 400
    
    progress, error = progress_service.update_progress(
        current_user.id,
        training_id,
        slide_index
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'success': True,
        'progress': {
            'current_slide_index': progress.current_slide_index,
            'completed_slides': progress.completed_slides,
            'status': progress.status,
            'completion_percentage': progress.completion_percentage
        }
    })


@bp.route('/<int:training_id>/complete', methods=['POST'])
@login_required
def complete_training(training_id):
    """
    Mark training as complete.
    
    POST /trainings/<id>/complete
    """
    success, error = progress_service.complete_training(current_user.id, training_id)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'success': True,
        'message': 'Formation complétée avec succès!'
    })


@bp.route('/<int:training_id>/slides/<int:slide_index>')
@login_required
def get_slide(training_id, slide_index):
    """
    Get a specific slide (AJAX).
    
    GET /trainings/<id>/slides/<index>
    """
    training = training_service.get_training_by_id(training_id)
    
    if not training or not training.is_published:
        return jsonify({'error': 'Formation introuvable'}), 404
    
    if not training.is_targeted_to_user(current_user):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    # Validate slide index
    if slide_index < 0 or slide_index >= len(training.slides):
        return jsonify({'error': 'Index de diapositive invalide'}), 400
    
    slide_data = training.slides[slide_index]
    
    # Render slide HTML
    slide_html = render_slide(slide_data)
    
    # Mark slide as completed
    progress_service.complete_slide(current_user.id, training_id, slide_index)
    
    return jsonify({
        'success': True,
        'slide': {
            'index': slide_index,
            'type': slide_data.get('type'),
            'html': slide_html,
            'data': slide_data
        }
    })


@bp.route('/history')
@login_required
def training_history():
    """
    View user's training history.
    
    GET /history
    """
    # Get all training progress for user
    progress_records = progress_service.get_user_training_history(current_user.id).all()
    
    # Organize by status
    history_data = {
        'completed': [],
        'in_progress': [],
        'not_started': []
    }
    
    for progress in progress_records:
        if progress.training and progress.training.is_published:
            history_data[progress.status].append({
                'progress': progress,
                'training': progress.training,
                'completion_percentage': progress.completion_percentage
            })
    
    return render_template('training/history.html', history_data=history_data)
