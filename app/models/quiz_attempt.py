"""
QuizAttempt model for tracking user quiz attempts and results.
"""

from datetime import datetime
from app import db


class QuizAttempt(db.Model):
    """
    QuizAttempt model for recording individual quiz attempts by users.
    
    Tracks answers given, scores, pass/fail status, and timing.
    """
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    
    # Answers given as JSON: {question_id: [selected_answer_indices], ...}
    answers_given = db.Column(db.JSON, nullable=False, default=dict)
    
    # Score achieved (percentage 0-100)
    score = db.Column(db.Float, nullable=False, default=0)
    
    # Whether minimum score was achieved
    passed = db.Column(db.Boolean, nullable=False, default=False)
    
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Time taken in seconds
    time_taken = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<QuizAttempt user_id={self.user_id} quiz_id={self.quiz_id} score={self.score}>'
    
    def calculate_score(self):
        """
        Calculate score based on answers given.
        
        Returns:
            tuple: (score_percentage, points_earned, total_points)
        """
        if not self.quiz or not self.answers_given:
            return 0, 0, 0
        
        points_earned = 0
        total_points = 0
        
        for question in self.quiz.questions:
            total_points += question.points
            
            # Get user's answer for this question
            user_answer = self.answers_given.get(str(question.id))
            if user_answer is None:
                continue
            
            # Check if answer is correct
            if question.check_answer(user_answer):
                points_earned += question.points
        
        # Calculate percentage
        if total_points > 0:
            score_percentage = (points_earned / total_points) * 100
        else:
            score_percentage = 0
        
        return score_percentage, points_earned, total_points
    
    def submit(self):
        """
        Submit the quiz attempt and calculate final score.
        """
        self.completed_at = datetime.utcnow()
        
        # Calculate time taken
        if self.started_at and self.completed_at:
            time_delta = self.completed_at - self.started_at
            self.time_taken = int(time_delta.total_seconds())
        
        # Calculate score
        score_percentage, _, _ = self.calculate_score()
        self.score = score_percentage
        
        # Check if passed
        self.passed = self.score >= self.quiz.minimum_score
    
    @property
    def is_completed(self):
        """Check if attempt is completed."""
        return self.completed_at is not None
    
    @property
    def is_in_progress(self):
        """Check if attempt is in progress."""
        return self.completed_at is None
