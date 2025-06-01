from datetime import datetime
from sqlalchemy import Text, JSON
from sqlalchemy.exc import IntegrityError
import logging
from __init__ import app, db

class BorderFeedback(db.Model):
    """
    BorderFeedback Model
    
    The BorderFeedback class represents user feedback about border crossing experiences.
    
    Attributes:
        id (db.Column): The primary key, an integer representing the unique identifier for the feedback.
        _time_cross (db.Column): Timestamp when the user crossed the border.
        _time_taken (db.Column): Actual time it took to cross the border (minutes).
        _time_diff (db.Column): Difference between estimated and actual wait time (minutes).
        _user_message (db.Column): User's message about their crossing experience.
        _created_at (db.Column): Timestamp when the feedback was submitted.
    """
    __tablename__ = 'border_feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    _time_cross = db.Column(db.DateTime, nullable=False)
    _time_taken = db.Column(db.Float, nullable=False)
    _time_diff = db.Column(db.Float, nullable=False)
    _user_message = db.Column(db.Text, nullable=False)
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, time_cross, time_taken, time_diff, user_message):
        """
        Constructor, 1st step in object creation.
        
        Args:
            time_cross (datetime): When the user crossed the border.
            time_taken (float): Actual time it took to cross the border in minutes.
            time_diff (float): Difference between estimated and actual wait time in minutes.
            user_message (str): Required message about the experience.
        """
        self._time_cross = time_cross
        self._time_taken = time_taken
        self._time_diff = time_diff
        self._user_message = user_message

    def __repr__(self):
        """
        String representation of the BorderFeedback object.
        
        Returns:
            str: A text representation of the object.
        """
        return f"BorderFeedback(id={self.id}, time_cross={self._time_cross}, time_taken={self._time_taken}, time_diff={self._time_diff})"
    
    def create(self):
        """
        Creates a new feedback record in the database.
        
        Returns:
            BorderFeedback: The created feedback object, or None on error.
        """
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            logging.warning(f"IntegrityError: Could not create feedback due to {str(e)}.")
            return None
        return self
    
    def read(self):
        """
        Returns the feedback data as a dictionary.
        
        Returns:
            dict: A dictionary containing the feedback data.
        """
        return {
            "id": self.id,
            "time_cross": self._time_cross.isoformat() if self._time_cross else None,
            "time_taken": self._time_taken,
            "time_diff": self._time_diff,
            "user_message": self._user_message,
            "created_at": self._created_at.isoformat() if self._created_at else None
        }
    
    def update(self, data):
        """
        Updates the feedback with new data.
        
        Args:
            data (dict): A dictionary containing the new data.
            
        Returns:
            BorderFeedback: The updated feedback object, or None on error.
        """
        if 'time_cross' in data and data['time_cross']:
            self._time_cross = data['time_cross']
        if 'time_taken' in data and data['time_taken'] is not None:
            self._time_taken = data['time_taken']
        if 'time_diff' in data and data['time_diff'] is not None:
            self._time_diff = data['time_diff']
        if 'user_message' in data:
            self._user_message = data['user_message']
            
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            logging.warning(f"IntegrityError: Could not update feedback with id {self.id}.")
            return None
        return self
    
    def delete(self):
        """
        Deletes the feedback from the database.
        """
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
            
    @staticmethod
    def get_recent_feedback(limit=10):
        """
        Get recent feedback submissions.
        
        Args:
            limit (int): Maximum number of records to return.
            
        Returns:
            list: List of dictionaries containing feedback data.
        """
        feedbacks = BorderFeedback.query.order_by(BorderFeedback._created_at.desc()).limit(limit).all()
        return [feedback.read() for feedback in feedbacks]


def initBorderFeedbacks():
    """
    Initialize the BorderFeedback table.
    """
    with app.app_context():
        """Create database and tables"""
        db.create_all()
        print("BorderFeedback table created or verified successfully")