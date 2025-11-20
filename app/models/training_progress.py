"""
TrainingProgress model for tracking user progress through trainings.
"""

from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified
from app import db


class TrainingProgress(db.Model):
    """
    TrainingProgress model for tracking individual user progress through trainings.
    
    Tracks current position, completed slides, quiz attempts, and overall status.
    """
    __tablename__ = 'training_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    training_id = db.Column(db.Integer, db.ForeignKey('trainings.id'), nullable=False)
    
    current_slide_index = db.Column(db.Integer, default=0, nullable=False)
    
    # Array of completed slide indices
    completed_slides = db.Column(db.JSON, default=list)
    
    # Array of quiz attempt records: [{quiz_id, attempt_id, score, passed, timestamp}, ...]
    quiz_attempts = db.Column(db.JSON, default=list)
    
    # Status: 'not_started', 'in_progress', 'completed'
    status = db.Column(db.String(20), default='not_started', nullable=False)
    
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    last_accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure unique progress record per user-training combination
    __table_args__ = (
        db.UniqueConstraint('user_id', 'training_id', name='unique_user_training'),
        db.Index('idx_user_training', 'user_id', 'training_id'),
    )
    
    def __repr__(self):
        return f'<TrainingProgress user_id={self.user_id} training_id={self.training_id}>'
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage."""
        if not self.training or not self.training.slide_count:
            return 0
        completed_count = len(self.completed_slides) if self.completed_slides else 0
        return int((completed_count / self.training.slide_count) * 100)
    
    def mark_slide_completed(self, slide_index):
        """
        Mark a slide as completed.
        
        Args:
            slide_index: Index of the slide to mark as completed
        """
        if self.completed_slides is None:
            self.completed_slides = []
        
        if slide_index not in self.completed_slides:
            self.completed_slides.append(slide_index)
            # SQLAlchemy requires explicit flag for JSON field updates
            flag_modified(self, 'completed_slides')
        
        # Update status
        if self.status == 'not_started':
            self.status = 'in_progress'
            self.started_at = datetime.utcnow()
        
        self.last_accessed_at = datetime.utcnow()
    
    def add_quiz_attempt(self, quiz_id, attempt_id, score, passed):
        """
        Record a quiz attempt.
        
        Args:
            quiz_id: ID of the quiz
            attempt_id: ID of the quiz attempt
            score: Score achieved
            passed: Whether the quiz was passed
        """
        if self.quiz_attempts is None:
            self.quiz_attempts = []
        
        self.quiz_attempts.append({
            'quiz_id': quiz_id,
            'attempt_id': attempt_id,
            'score': score,
            'passed': passed,
            'timestamp': datetime.utcnow().isoformat()
        })
        flag_modified(self, 'quiz_attempts')
        self.last_accessed_at = datetime.utcnow()
    
    def mark_completed(self):
        """Mark the training as completed."""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.last_accessed_at = datetime.utcnow()
