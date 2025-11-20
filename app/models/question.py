"""
Question model for quiz questions.
"""

from app import db


class Question(db.Model):
    """
    Question model for quiz questions with multiple or single choice answers.
    
    Answers are stored as JSON with correct answers marked and optional explanations.
    """
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    
    # Type: 'multiple_choice' (multiple correct) or 'single_choice' (one correct)
    question_type = db.Column(db.String(20), nullable=False, default='single_choice')
    
    # Answers as JSON array: [{text: '...', is_correct: true/false, explanation: '...'}, ...]
    answers = db.Column(db.JSON, nullable=False, default=list)
    
    # Points awarded for correct answer
    points = db.Column(db.Integer, default=1, nullable=False)
    
    # Order of question in quiz
    order_index = db.Column(db.Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f'<Question {self.id}: {self.question_text[:50]}>'
    
    @property
    def correct_answers(self):
        """Get list of correct answer indices."""
        if not self.answers:
            return []
        return [i for i, answer in enumerate(self.answers) if answer.get('is_correct', False)]
    
    def check_answer(self, selected_indices):
        """
        Check if selected answer indices are correct.
        
        Args:
            selected_indices: List of selected answer indices
            
        Returns:
            bool: True if answer is correct
        """
        correct = set(self.correct_answers)
        selected = set(selected_indices if isinstance(selected_indices, list) else [selected_indices])
        
        if self.question_type == 'single_choice':
            # For single choice, exactly one answer must be selected and correct
            return len(selected) == 1 and selected == correct
        else:
            # For multiple choice, all correct answers must be selected
            return selected == correct
    
    def get_randomized_answers(self):
        """
        Get answers in randomized order.
        
        Returns:
            list: Answers with their original indices preserved
        """
        import random
        if not self.answers:
            return []
        
        # Create list of (index, answer) tuples
        indexed_answers = list(enumerate(self.answers))
        # Shuffle
        random.shuffle(indexed_answers)
        return indexed_answers
