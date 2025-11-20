"""
Training model for managing educational content.
"""

from datetime import datetime
from app import db


class Training(db.Model):
    """
    Training model for managing educational content and courses.
    
    Includes slides, targeting options, and publication status.
    """
    __tablename__ = 'trainings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Slides as JSON array: [{type: 'text|video|image', content: '...', duration: 60}, ...]
    slides = db.Column(db.JSON, nullable=False, default=list)
    
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    is_mandatory = db.Column(db.Boolean, default=False, nullable=False)
    
    # Targeting options as JSON arrays
    target_roles = db.Column(db.JSON, default=list)  # ['admin', 'manager', 'user']
    target_teams = db.Column(db.JSON, default=list)  # ['Sales', 'Engineering', ...]
    target_locations = db.Column(db.JSON, default=list)  # ['Paris', 'Lyon', ...]
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    progress_records = db.relationship('TrainingProgress', backref='training', lazy='dynamic', cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='training', lazy='dynamic')
    
    def __repr__(self):
        return f'<Training {self.title}>'
    
    @property
    def slide_count(self):
        """Get total number of slides."""
        return len(self.slides) if self.slides else 0
    
    def is_targeted_to_user(self, user):
        """
        Check if training is targeted to a specific user.
        
        Args:
            user: User instance to check targeting for
            
        Returns:
            bool: True if training targets this user
        """
        # If no targeting criteria, training is for everyone
        if not self.target_roles and not self.target_teams and not self.target_locations:
            return True
        
        # Check role targeting
        if self.target_roles and user.role and user.role.name in self.target_roles:
            return True
        
        # Check team targeting
        if self.target_teams and user.team in self.target_teams:
            return True
        
        # Check location targeting
        if self.target_locations and user.location in self.target_locations:
            return True
        
        return False
