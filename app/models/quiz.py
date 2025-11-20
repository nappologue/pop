"""
Quiz model for assessments and evaluations.
"""

from datetime import datetime
from app import db


class Quiz(db.Model):
    """
    Quiz model for creating assessments within trainings or as standalone.
    
    Supports question pools, time limits, passing scores, and randomization.
    """
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    training_id = db.Column(db.Integer, db.ForeignKey('trainings.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Number of questions to randomly select from pool (null = all questions)
    question_pool_size = db.Column(db.Integer)
    
    # Minimum score percentage to pass (0-100)
    minimum_score = db.Column(db.Integer, default=70, nullable=False)
    
    # Time limit in minutes (null = no limit)
    time_limit = db.Column(db.Integer)
    
    # Whether failing this quiz blocks progress
    is_eliminatory = db.Column(db.Boolean, default=False, nullable=False)
    
    # Position in training (null for standalone quizzes or end-of-training)
    position_in_training = db.Column(db.Integer)
    
    # Whether to randomize answer order
    randomize_answers = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy='dynamic', cascade='all, delete-orphan', order_by='Question.order_index')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic')
    
    def __repr__(self):
        return f'<Quiz {self.title}>'
    
    @property
    def is_standalone(self):
        """Check if quiz is standalone (not part of a training)."""
        return self.training_id is None
    
    @property
    def total_questions(self):
        """Get total number of questions in the quiz."""
        return self.questions.count()
    
    @property
    def total_points(self):
        """Calculate total possible points."""
        return sum(q.points for q in self.questions.all())
    
    def get_questions_for_attempt(self):
        """
        Get questions for a quiz attempt.
        
        Returns:
            list: Questions selected for this attempt (randomized if pool_size is set)
        """
        all_questions = self.questions.all()
        
        # If question_pool_size is set and less than total, randomly select
        if self.question_pool_size and self.question_pool_size < len(all_questions):
            import random
            return random.sample(all_questions, self.question_pool_size)
        
        return all_questions
