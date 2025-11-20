"""
Admin training routes blueprint for training management.

This module provides routes for administrators to create, edit, publish,
and assign trainings.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user
from app import db
from app.utils.auth import login_required, permission_required
from app.services import training_service, progress_service
from app.models import Training, User, Role
from app.utils.validators import validate_training_data, validate_slide_structure

bp = Blueprint('admin_training', __name__, url_prefix='/admin/trainings')


@bp.route('/')
@login_required
@permission_required('manage_trainings')
def list_trainings():
    """
    List all trainings with filters.
    
    GET /admin/trainings
    """
    # Get filter parameters
    filters = {}
    
    if request.args.get('is_published'):
        filters['is_published'] = request.args.get('is_published') == 'true'
    
    if request.args.get('is_mandatory'):
        filters['is_mandatory'] = request.args.get('is_mandatory') == 'true'
    
    if request.args.get('search'):
        filters['search'] = request.args.get('search')
    
    if request.args.get('created_by'):
        filters['created_by'] = int(request.args.get('created_by'))
    
    # Get trainings with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    trainings_query = training_service.get_all_trainings(filters)
    trainings_pagination = trainings_query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template(
        'admin/trainings/list.html',
        trainings=trainings_pagination.items,
        pagination=trainings_pagination,
        filters=filters
    )


@bp.route('/create', methods=['GET'])
@login_required
@permission_required('manage_trainings')
def create_form():
    """
    Display training creation form.
    
    GET /admin/trainings/create
    """
    # Get available roles, teams, locations for targeting
    roles = Role.query.all()
    teams = db.session.query(User.team).filter(User.team.isnot(None)).distinct().all()
    teams = [t[0] for t in teams]
    locations = db.session.query(User.location).filter(User.location.isnot(None)).distinct().all()
    locations = [l[0] for l in locations]
    
    return render_template(
        'admin/trainings/create.html',
        roles=roles,
        teams=teams,
        locations=locations
    )


@bp.route('/create', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def create_training():
    """
    Handle training creation.
    
    POST /admin/trainings/create
    """
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    # Parse slides from JSON if coming from form
    if 'slides' in data and isinstance(data['slides'], str):
        import json
        try:
            data['slides'] = json.loads(data['slides'])
        except json.JSONDecodeError:
            return jsonify({'error': 'Format de diapositives invalide'}), 400
    
    # Parse targeting arrays
    for field in ['target_roles', 'target_teams', 'target_locations']:
        if field in data:
            if isinstance(data[field], str):
                import json
                try:
                    data[field] = json.loads(data[field])
                except json.JSONDecodeError:
                    data[field] = []
    
    # Convert boolean fields
    data['is_mandatory'] = data.get('is_mandatory') in [True, 'true', 'on', '1']
    
    # Validate data
    is_valid, errors = validate_training_data(data)
    
    if not is_valid:
        if request.is_json:
            return jsonify({'error': ' '.join(errors)}), 400
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('admin_training.create_form'))
    
    # Create training
    training, error = training_service.create_training(data, current_user.id)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('admin_training.create_form'))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'training_id': training.id,
            'message': 'Formation créée avec succès'
        })
    
    flash('Formation créée avec succès!', 'success')
    return redirect(url_for('admin_training.edit_form', training_id=training.id))


@bp.route('/<int:training_id>/edit', methods=['GET'])
@login_required
@permission_required('manage_trainings')
def edit_form(training_id):
    """
    Display training edit form.
    
    GET /admin/trainings/<id>/edit
    """
    training = training_service.get_training_by_id(training_id)
    
    if not training:
        flash('Formation introuvable.', 'danger')
        return redirect(url_for('admin_training.list_trainings'))
    
    # Get available roles, teams, locations for targeting
    roles = Role.query.all()
    teams = db.session.query(User.team).filter(User.team.isnot(None)).distinct().all()
    teams = [t[0] for t in teams]
    locations = db.session.query(User.location).filter(User.location.isnot(None)).distinct().all()
    locations = [l[0] for l in locations]
    
    return render_template(
        'admin/trainings/edit.html',
        training=training,
        roles=roles,
        teams=teams,
        locations=locations
    )


@bp.route('/<int:training_id>/edit', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def update_training(training_id):
    """
    Handle training update.
    
    POST /admin/trainings/<id>/edit
    """
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    # Parse slides from JSON if coming from form
    if 'slides' in data and isinstance(data['slides'], str):
        import json
        try:
            data['slides'] = json.loads(data['slides'])
        except json.JSONDecodeError:
            return jsonify({'error': 'Format de diapositives invalide'}), 400
    
    # Parse targeting arrays
    for field in ['target_roles', 'target_teams', 'target_locations']:
        if field in data:
            if isinstance(data[field], str):
                import json
                try:
                    data[field] = json.loads(data[field])
                except json.JSONDecodeError:
                    data[field] = []
    
    # Convert boolean fields
    if 'is_mandatory' in data:
        data['is_mandatory'] = data.get('is_mandatory') in [True, 'true', 'on', '1']
    
    # Validate data
    is_valid, errors = validate_training_data(data)
    
    if not is_valid:
        if request.is_json:
            return jsonify({'error': ' '.join(errors)}), 400
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('admin_training.edit_form', training_id=training_id))
    
    # Update training
    training, error = training_service.update_training(training_id, data)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('admin_training.edit_form', training_id=training_id))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Formation mise à jour avec succès'
        })
    
    flash('Formation mise à jour avec succès!', 'success')
    return redirect(url_for('admin_training.edit_form', training_id=training_id))


@bp.route('/<int:training_id>/delete', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def delete_training(training_id):
    """
    Soft delete a training.
    
    POST /admin/trainings/<id>/delete
    """
    success, error = training_service.delete_training(training_id)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('admin_training.list_trainings'))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Formation supprimée avec succès'
        })
    
    flash('Formation supprimée avec succès!', 'success')
    return redirect(url_for('admin_training.list_trainings'))


@bp.route('/<int:training_id>/preview')
@login_required
@permission_required('manage_trainings')
def preview_training(training_id):
    """
    Preview a training.
    
    GET /admin/trainings/<id>/preview
    """
    training = training_service.get_training_by_id(training_id)
    
    if not training:
        flash('Formation introuvable.', 'danger')
        return redirect(url_for('admin_training.list_trainings'))
    
    return render_template(
        'admin/trainings/preview.html',
        training=training
    )


@bp.route('/<int:training_id>/publish', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def publish_training(training_id):
    """
    Publish a training.
    
    POST /admin/trainings/<id>/publish
    """
    success, error = training_service.publish_training(training_id)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
    else:
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Formation publiée avec succès'
            })
        flash('Formation publiée avec succès!', 'success')
    
    return redirect(url_for('admin_training.edit_form', training_id=training_id))


@bp.route('/<int:training_id>/assign', methods=['GET'])
@login_required
@permission_required('manage_trainings')
def assign_form(training_id):
    """
    Display training assignment interface.
    
    GET /admin/trainings/<id>/assign
    """
    training = training_service.get_training_by_id(training_id)
    
    if not training:
        flash('Formation introuvable.', 'danger')
        return redirect(url_for('admin_training.list_trainings'))
    
    # Get available roles, teams, locations
    roles = Role.query.all()
    teams = db.session.query(User.team).filter(User.team.isnot(None)).distinct().all()
    teams = [t[0] for t in teams]
    locations = db.session.query(User.location).filter(User.location.isnot(None)).distinct().all()
    locations = [l[0] for l in locations]
    
    return render_template(
        'admin/trainings/assign.html',
        training=training,
        roles=roles,
        teams=teams,
        locations=locations
    )


@bp.route('/<int:training_id>/assign', methods=['POST'])
@login_required
@permission_required('manage_trainings')
def assign_training(training_id):
    """
    Handle bulk training assignment.
    
    POST /admin/trainings/<id>/assign
    """
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    # Parse arrays from form data
    user_criteria = {}
    
    if 'roles' in data:
        if isinstance(data['roles'], str):
            import json
            try:
                user_criteria['roles'] = json.loads(data['roles'])
            except json.JSONDecodeError:
                user_criteria['roles'] = [r.strip() for r in data['roles'].split(',') if r.strip()]
        else:
            user_criteria['roles'] = data['roles']
    
    if 'teams' in data:
        if isinstance(data['teams'], str):
            import json
            try:
                user_criteria['teams'] = json.loads(data['teams'])
            except json.JSONDecodeError:
                user_criteria['teams'] = [t.strip() for t in data['teams'].split(',') if t.strip()]
        else:
            user_criteria['teams'] = data['teams']
    
    if 'locations' in data:
        if isinstance(data['locations'], str):
            import json
            try:
                user_criteria['locations'] = json.loads(data['locations'])
            except json.JSONDecodeError:
                user_criteria['locations'] = [l.strip() for l in data['locations'].split(',') if l.strip()]
        else:
            user_criteria['locations'] = data['locations']
    
    # Assign training
    success, error = training_service.assign_training_to_users(training_id, user_criteria)
    
    if error:
        if request.is_json:
            return jsonify({'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('admin_training.assign_form', training_id=training_id))
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Formation affectée avec succès'
        })
    
    flash('Formation affectée avec succès!', 'success')
    return redirect(url_for('admin_training.edit_form', training_id=training_id))
