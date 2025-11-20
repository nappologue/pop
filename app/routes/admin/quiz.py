"""
Admin quiz routes blueprint for quiz management.

This module provides routes for administrators to create, edit, and manage
quizzes and questions.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user
from app import db
from app.utils.auth import login_required, permission_required
from app.services import quiz_service, quiz_attempt_service, training_service
from app.models import Training, QuizAttempt

bp = Blueprint('admin_quiz', __name__, url_prefix='/admin/quizzes')


@bp.route('/')
@login_required
@permission_required('manage_trainings')
def list_quizzes():
    """
    List all quizzes with filters.
    
    GET /admin/quizzes
    """
    # Get filter parameters
    filters = {}
    
    if request.args.get('training_id'):
        filters['training_id'] = int(request.args.get('training_id'))
    elif request.args.get('standalone') == 'true':
        filters['training_id'] = None
    
    if request.args.get('is_eliminatory'):
        filters['is_eliminatory'] = request.args.get('is_eliminatory') == 'true'
    
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    # Get quizzes with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    quizzes_query = quiz_service.get_all_quizzes(filters)
    quizzes_pagination = quizzes_query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Get all trainings for filter dropdown
    trainings = Training.query.all()
    
    return render_template(
        'admin/quizzes/list.html',
        quizzes=quizzes_pagination.items,
        pagination=quizzes_pagination,
        filters=filters,
        trainings=trainings
    )


@bp.route('/create', methods=['GET'])
@login_required
@permission_required('manage_trainings')
def create_form():
    """
    Display quiz creation form.
    
    GET /admin/quizzes/create
    """
    # Get trainings for dropdown
    trainings = Training.query.all()
    
    return render_template(
        'admin/quizzes/create.html',
        trainings=trainings
    )


@bp.route('/create', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def create_quiz():
    """
    Handle quiz creation.
    
    POST /admin/quizzes/create
    """
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    # Convert numeric fields
    if 'question_pool_size' in data and data['question_pool_size']:
        data['question_pool_size'] = int(data['question_pool_size'])
    
    if 'minimum_score' in data and data['minimum_score']:
        data['minimum_score'] = int(data['minimum_score'])
    
    if 'time_limit' in data and data['time_limit']:
        data['time_limit'] = int(data['time_limit'])
    
    if 'position_in_training' in data and data['position_in_training']:
        data['position_in_training'] = int(data['position_in_training'])
    
    if 'training_id' in data and data['training_id']:
        data['training_id'] = int(data['training_id']) if data['training_id'] != '' else None
    else:
        data['training_id'] = None
    
    # Convert boolean fields
    data['is_eliminatory'] = data.get('is_eliminatory') in [True, 'true', 'on', '1']
    data['randomize_answers'] = data.get('randomize_answers', True) in [True, 'true', 'on', '1']
    
    # Create quiz
    quiz, error = quiz_service.create_quiz(data)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('admin_quiz.create_form'))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'quiz_id': quiz.id,
            'message': 'Quiz créé avec succès'
        })
    
    flash('Quiz créé avec succès!', 'success')
    return redirect(url_for('admin_quiz.edit_form', quiz_id=quiz.id))


@bp.route('/<int:quiz_id>/edit', methods=['GET'])
@login_required
@permission_required('manage_trainings')
def edit_form(quiz_id):
    """
    Display quiz edit form (quiz settings + questions).
    
    GET /admin/quizzes/<id>/edit
    """
    quiz = quiz_service.get_quiz_by_id(quiz_id)
    
    if not quiz:
        flash('Quiz introuvable.', 'danger')
        return redirect(url_for('admin_quiz.list_quizzes'))
    
    # Get trainings for dropdown
    trainings = Training.query.all()
    
    # Get questions
    questions = quiz.questions.order_by('order_index').all()
    
    return render_template(
        'admin/quizzes/edit.html',
        quiz=quiz,
        questions=questions,
        trainings=trainings
    )


@bp.route('/<int:quiz_id>/edit', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def update_quiz(quiz_id):
    """
    Handle quiz update.
    
    POST /admin/quizzes/<id>/edit
    """
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    # Convert numeric fields
    if 'question_pool_size' in data:
        data['question_pool_size'] = int(data['question_pool_size']) if data['question_pool_size'] else None
    
    if 'minimum_score' in data:
        data['minimum_score'] = int(data['minimum_score']) if data['minimum_score'] else 70
    
    if 'time_limit' in data:
        data['time_limit'] = int(data['time_limit']) if data['time_limit'] else None
    
    if 'position_in_training' in data:
        data['position_in_training'] = int(data['position_in_training']) if data['position_in_training'] else None
    
    # Convert boolean fields
    if 'is_eliminatory' in data:
        data['is_eliminatory'] = data.get('is_eliminatory') in [True, 'true', 'on', '1']
    
    if 'randomize_answers' in data:
        data['randomize_answers'] = data.get('randomize_answers') in [True, 'true', 'on', '1']
    
    # Update quiz
    quiz, error = quiz_service.update_quiz(quiz_id, data)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('admin_quiz.edit_form', quiz_id=quiz_id))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Quiz mis à jour avec succès'
        })
    
    flash('Quiz mis à jour avec succès!', 'success')
    return redirect(url_for('admin_quiz.edit_form', quiz_id=quiz_id))


@bp.route('/<int:quiz_id>/delete', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def delete_quiz(quiz_id):
    """
    Delete a quiz.
    
    POST /admin/quizzes/<id>/delete
    """
    success, error = quiz_service.delete_quiz(quiz_id)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('admin_quiz.list_quizzes'))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Quiz supprimé avec succès'
        })
    
    flash('Quiz supprimé avec succès!', 'success')
    return redirect(url_for('admin_quiz.list_quizzes'))


@bp.route('/<int:quiz_id>/questions', methods=['GET'])
@login_required
@permission_required('manage_trainings')
def manage_questions(quiz_id):
    """
    Manage questions for a quiz.
    
    GET /admin/quizzes/<id>/questions
    """
    quiz = quiz_service.get_quiz_by_id(quiz_id)
    
    if not quiz:
        flash('Quiz introuvable.', 'danger')
        return redirect(url_for('admin_quiz.list_quizzes'))
    
    questions = quiz.questions.order_by('order_index').all()
    
    return render_template(
        'admin/quizzes/questions.html',
        quiz=quiz,
        questions=questions
    )


@bp.route('/<int:quiz_id>/questions/add', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def add_question(quiz_id):
    """
    Add a new question to a quiz.
    
    POST /admin/quizzes/<id>/questions/add
    """
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    # Parse answers JSON
    if 'answers' in data and isinstance(data['answers'], str):
        import json
        try:
            data['answers'] = json.loads(data['answers'])
        except json.JSONDecodeError:
            return jsonify({'error': 'Format de réponses invalide'}), 400
    
    # Convert numeric fields
    if 'points' in data:
        data['points'] = int(data['points']) if data['points'] else 1
    
    if 'order_index' in data:
        data['order_index'] = int(data['order_index']) if data['order_index'] else None
    
    # Add question
    question, error = quiz_service.add_question_to_quiz(quiz_id, data)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('admin_quiz.manage_questions', quiz_id=quiz_id))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'question_id': question.id,
            'message': 'Question ajoutée avec succès'
        })
    
    flash('Question ajoutée avec succès!', 'success')
    return redirect(url_for('admin_quiz.manage_questions', quiz_id=quiz_id))


@bp.route('/<int:quiz_id>/questions/<int:question_id>/edit', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def edit_question(quiz_id, question_id):
    """
    Edit an existing question.
    
    POST /admin/quizzes/<id>/questions/<q_id>/edit
    """
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    # Parse answers JSON
    if 'answers' in data and isinstance(data['answers'], str):
        import json
        try:
            data['answers'] = json.loads(data['answers'])
        except json.JSONDecodeError:
            return jsonify({'error': 'Format de réponses invalide'}), 400
    
    # Convert numeric fields
    if 'points' in data:
        data['points'] = int(data['points']) if data['points'] else 1
    
    if 'order_index' in data:
        data['order_index'] = int(data['order_index']) if data['order_index'] else None
    
    # Update question
    question, error = quiz_service.update_question(question_id, data)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('admin_quiz.manage_questions', quiz_id=quiz_id))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Question mise à jour avec succès'
        })
    
    flash('Question mise à jour avec succès!', 'success')
    return redirect(url_for('admin_quiz.manage_questions', quiz_id=quiz_id))


@bp.route('/<int:quiz_id>/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def delete_question(quiz_id, question_id):
    """
    Delete a question from a quiz.
    
    POST /admin/quizzes/<id>/questions/<q_id>/delete
    """
    success, error = quiz_service.delete_question(question_id)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('admin_quiz.manage_questions', quiz_id=quiz_id))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Question supprimée avec succès'
        })
    
    flash('Question supprimée avec succès!', 'success')
    return redirect(url_for('admin_quiz.manage_questions', quiz_id=quiz_id))


@bp.route('/<int:quiz_id>/attempts', methods=['GET'])
@login_required
@permission_required('manage_trainings')
def view_attempts(quiz_id):
    """
    View all attempts for a quiz (admin overview).
    
    GET /admin/quizzes/<id>/attempts
    """
    quiz = quiz_service.get_quiz_by_id(quiz_id)
    
    if not quiz:
        flash('Quiz introuvable.', 'danger')
        return redirect(url_for('admin_quiz.list_quizzes'))
    
    # Get all attempts for this quiz
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    attempts_query = QuizAttempt.query.filter_by(
        quiz_id=quiz_id
    ).order_by(QuizAttempt.started_at.desc())
    
    attempts_pagination = attempts_query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Get quiz statistics
    stats = quiz_attempt_service.get_quiz_statistics(quiz_id)
    
    return render_template(
        'admin/quizzes/attempts.html',
        quiz=quiz,
        attempts=attempts_pagination.items,
        pagination=attempts_pagination,
        stats=stats
    )
