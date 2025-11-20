"""
Quiz routes blueprint for user-facing quiz functionality.

This module provides routes for users to take quizzes, submit answers,
and view their results.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import current_user
from app.utils.auth import login_required
from app.services import quiz_service, quiz_attempt_service

bp = Blueprint('quiz', __name__, url_prefix='/quiz')


@bp.route('/<int:quiz_id>/start', methods=['GET'])
@login_required
def start_quiz_page(quiz_id):
    """
    Display quiz start page with instructions.
    
    GET /quiz/<id>/start
    """
    quiz = quiz_service.get_quiz_by_id(quiz_id)
    
    if not quiz:
        flash('Quiz introuvable.', 'danger')
        return redirect(url_for('training.list_trainings'))
    
    # Check if user can take the quiz
    can_retake, reason = quiz_attempt_service.can_retake_quiz(current_user.id, quiz_id)
    
    # Get user's previous attempts
    previous_attempts = quiz_attempt_service.get_user_attempts(
        current_user.id, 
        quiz_id
    ).all()
    
    return render_template(
        'quiz/instructions.html',
        quiz=quiz,
        can_retake=can_retake,
        retake_reason=reason,
        previous_attempts=previous_attempts
    )


@bp.route('/<int:quiz_id>/start', methods=['POST'])
@login_required
def start_quiz_attempt(quiz_id):
    """
    Generate quiz instance and begin a new attempt.
    
    POST /quiz/<id>/start
    """
    quiz = quiz_service.get_quiz_by_id(quiz_id)
    
    if not quiz:
        return jsonify({'error': 'Quiz introuvable'}), 404
    
    # Check if user can take the quiz
    can_retake, reason = quiz_attempt_service.can_retake_quiz(current_user.id, quiz_id)
    if not can_retake:
        return jsonify({'error': reason}), 400
    
    # Generate quiz instance
    quiz_instance = quiz_service.generate_quiz_instance(quiz_id)
    
    if not quiz_instance:
        return jsonify({'error': 'Impossible de générer le quiz'}), 500
    
    # Start attempt
    attempt, error = quiz_attempt_service.start_attempt(
        current_user.id,
        quiz_id,
        quiz_instance
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'success': True,
        'attempt_id': attempt.id,
        'redirect_url': url_for('quiz.take_quiz', quiz_id=quiz_id, attempt_id=attempt.id)
    })


@bp.route('/<int:quiz_id>/attempt/<int:attempt_id>', methods=['GET'])
@login_required
def take_quiz(quiz_id, attempt_id):
    """
    Quiz taking interface.
    
    GET /quiz/<id>/attempt/<attempt_id>
    """
    attempt = quiz_attempt_service.get_user_attempts(
        current_user.id, 
        quiz_id
    ).filter_by(id=attempt_id).first()
    
    if not attempt:
        flash('Tentative introuvable.', 'danger')
        return redirect(url_for('quiz.start_quiz_page', quiz_id=quiz_id))
    
    if attempt.is_completed:
        flash('Cette tentative est déjà terminée.', 'info')
        return redirect(url_for('quiz.view_results', quiz_id=quiz_id, attempt_id=attempt_id))
    
    # Get quiz instance data
    quiz_instance = attempt.answers_given.get('_quiz_instance', {})
    
    if not quiz_instance:
        flash('Erreur: instance de quiz invalide.', 'danger')
        return redirect(url_for('quiz.start_quiz_page', quiz_id=quiz_id))
    
    # Build questions data for display
    questions_display = []
    for question_id in quiz_instance.get('question_ids', []):
        question = None
        for q in attempt.quiz.questions:
            if q.id == question_id:
                question = q
                break
        
        if question:
            questions_display.append({
                'id': question.id,
                'text': question.question_text,
                'type': question.question_type,
                'answers': question.answers,
                'points': question.points
            })
    
    return render_template(
        'quiz/player.html',
        quiz=attempt.quiz,
        attempt=attempt,
        questions=questions_display,
        quiz_instance=quiz_instance
    )


@bp.route('/<int:quiz_id>/attempt/<int:attempt_id>/answer', methods=['POST'])
@login_required
def submit_answer(quiz_id, attempt_id):
    """
    Submit a single answer (AJAX).
    
    POST /quiz/<id>/attempt/<attempt_id>/answer
    Body: { "question_id": 1, "answer": 0 or [0, 1] }
    """
    data = request.get_json()
    
    if not data or 'question_id' not in data or 'answer' not in data:
        return jsonify({'error': 'Données invalides'}), 400
    
    question_id = data['question_id']
    answer = data['answer']
    
    # Verify attempt belongs to current user
    attempt = quiz_attempt_service.get_user_attempts(
        current_user.id,
        quiz_id
    ).filter_by(id=attempt_id).first()
    
    if not attempt:
        return jsonify({'error': 'Tentative introuvable'}), 404
    
    if attempt.is_completed:
        return jsonify({'error': 'Tentative déjà terminée'}), 400
    
    # Submit answer
    attempt, error = quiz_attempt_service.submit_answer(attempt_id, question_id, answer)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'success': True,
        'message': 'Réponse enregistrée'
    })


@bp.route('/<int:quiz_id>/attempt/<int:attempt_id>/complete', methods=['POST'])
@login_required
def complete_quiz(quiz_id, attempt_id):
    """
    Submit and finalize quiz attempt.
    
    POST /quiz/<id>/attempt/<attempt_id>/complete
    """
    # Verify attempt belongs to current user
    attempt = quiz_attempt_service.get_user_attempts(
        current_user.id,
        quiz_id
    ).filter_by(id=attempt_id).first()
    
    if not attempt:
        return jsonify({'error': 'Tentative introuvable'}), 404
    
    if attempt.is_completed:
        return jsonify({'error': 'Tentative déjà terminée'}), 400
    
    # Complete and grade attempt
    attempt, error = quiz_attempt_service.complete_attempt(attempt_id)
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'success': True,
        'passed': attempt.passed,
        'score': attempt.score,
        'redirect_url': url_for('quiz.view_results', quiz_id=quiz_id, attempt_id=attempt_id)
    })


@bp.route('/<int:quiz_id>/attempt/<int:attempt_id>/results', methods=['GET'])
@login_required
def view_results(quiz_id, attempt_id):
    """
    View results for a completed quiz attempt.
    
    GET /quiz/<id>/attempt/<attempt_id>/results
    """
    # Verify attempt belongs to current user
    attempt = quiz_attempt_service.get_user_attempts(
        current_user.id,
        quiz_id
    ).filter_by(id=attempt_id).first()
    
    if not attempt:
        flash('Tentative introuvable.', 'danger')
        return redirect(url_for('quiz.start_quiz_page', quiz_id=quiz_id))
    
    if not attempt.is_completed:
        flash('Cette tentative n\'est pas encore terminée.', 'warning')
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id, attempt_id=attempt_id))
    
    # Get results with feedback
    results = quiz_attempt_service.get_attempt_results(attempt_id)
    
    if not results:
        flash('Impossible de charger les résultats.', 'danger')
        return redirect(url_for('quiz.start_quiz_page', quiz_id=quiz_id))
    
    return render_template(
        'quiz/results.html',
        quiz=results['quiz'],
        attempt=results['attempt'],
        feedback=results['feedback']
    )


@bp.route('/<int:quiz_id>/attempts', methods=['GET'])
@login_required
def attempt_history(quiz_id):
    """
    View user's attempt history for a specific quiz.
    
    GET /quiz/<id>/attempts
    """
    quiz = quiz_service.get_quiz_by_id(quiz_id)
    
    if not quiz:
        flash('Quiz introuvable.', 'danger')
        return redirect(url_for('training.list_trainings'))
    
    # Get user's attempts
    attempts = quiz_attempt_service.get_user_attempts(
        current_user.id,
        quiz_id
    ).all()
    
    return render_template(
        'quiz/history.html',
        quiz=quiz,
        attempts=attempts
    )
