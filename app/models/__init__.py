"""
Models package for POP application.

Imports all database models for easy access.
"""

from app.models.role import Role
from app.models.user import User
from app.models.training import Training
from app.models.training_progress import TrainingProgress
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.quiz_attempt import QuizAttempt

__all__ = [
    'Role',
    'User',
    'Training',
    'TrainingProgress',
    'Quiz',
    'Question',
    'QuizAttempt',
]
