from datetime import datetime
from sqlalchemy import Text, JSON
from sqlalchemy.exc import IntegrityError
import logging
from __init__ import app, db

class TrafficReport(db.Model):
    """
    TrafficReport Model
    
    The TrafficReport class represents user reports about traffic incidents and conditions at border crossings.
    
    Attributes:
        id (db.Column): The primary key, an integer representing the unique identifier for the report.
        _report_time (db.Column): Timestamp when the incident occurred.
        _reason (db.Column): Type of incident (traffic, accident, natural disaster, etc.).
        _border_location (db.Column): Which border crossing (San Ysidro, Otay Mesa).
        _direction (db.Column): Direction of travel (entering us, entering mexico).
        _comments (db.Column): User's comments about the incident.
        _created_at (db.Column): Timestamp when the report was submitted.
    """
    __tablename__ = 'traffic_reports'

    id = db.Column(db.Integer, primary_key=True)
    _report_time = db.Column(db.DateTime, nullable=False)
    _reason = db.Column(db.String(100), nullable=False)
    _border_location = db.Column(db.String(50), nullable=False)
    _direction = db.Column(db.String(20), nullable=False)
    _comments = db.Column(db.Text, nullable=True)
    _created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, report_time, reason, border_location, direction, comments=""):
        """
        Constructor, 1st step in object creation.
        
        Args:
            report_time (datetime): When the incident occurred.
            reason (str): Type of incident.
            border_location (str): Which border crossing.
            direction (str): Direction of travel.
            comments (str): Optional comments about the incident.
        """
        self._report_time = report_time
        self._reason = reason
        self._border_location = border_location
        self._direction = direction
        self._comments = comments

    def __repr__(self):
        """
        String representation of the TrafficReport object.
        
        Returns:
            str: A text representation of the object.
        """
        return f"TrafficReport(id={self.id}, reason={self._reason}, border={self._border_location}, direction={self._direction})"
    
    def create(self):
        """
        Creates a new traffic report in the database.
        
        Returns:
            TrafficReport: The created report object, or None on error.
        """
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            logging.warning(f"IntegrityError: Could not create traffic report due to {str(e)}.")
            return None
        return self
    
    def read(self):
        """
        Returns the traffic report data as a dictionary.
        
        Returns:
            dict: A dictionary containing the report data.
        """
        return {
            "id": self.id,
            "report_time": self._report_time.isoformat() if self._report_time else None,
            "reason": self._reason,
            "border_location": self._border_location,
            "direction": self._direction,
            "comments": self._comments,
            "created_at": self._created_at.isoformat() if self._created_at else None
        }
    
    def update(self, data):
        """
        Updates the traffic report with new data.
        
        Args:
            data (dict): A dictionary containing the new data.
            
        Returns:
            TrafficReport: The updated report object, or None on error.
        """
        if 'report_time' in data and data['report_time']:
            self._report_time = data['report_time']
        if 'reason' in data and data['reason']:
            self._reason = data['reason']
        if 'border_location' in data and data['border_location']:
            self._border_location = data['border_location']
        if 'direction' in data and data['direction']:
            self._direction = data['direction']
        if 'comments' in data:
            self._comments = data['comments']
            
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            logging.warning(f"IntegrityError: Could not update traffic report with id {self.id}.")
            return None
        return self
    
    def delete(self):
        """
        Deletes the traffic report from the database.
        """
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
            
    @staticmethod
    def get_recent_reports(limit=10):
        """
        Get recent traffic reports.
        
        Args:
            limit (int): Maximum number of records to return.
            
        Returns:
            list: List of dictionaries containing report data.
        """
        reports = TrafficReport.query.order_by(TrafficReport._created_at.desc()).limit(limit).all()
        return [report.read() for report in reports]

    @staticmethod
    def get_reports_by_location(border_location, limit=20):
        """
        Get traffic reports by border location.
        
        Args:
            border_location (str): The border crossing location.
            limit (int): Maximum number of records to return.
            
        Returns:
            list: List of dictionaries containing report data.
        """
        reports = TrafficReport.query.filter_by(_border_location=border_location).order_by(TrafficReport._created_at.desc()).limit(limit).all()
        return [report.read() for report in reports]


def initTrafficReports():
    """
    Initialize the TrafficReport table.
    """
    with app.app_context():
        """Create database and tables"""
        db.create_all()
        print("TrafficReport table created or verified successfully")