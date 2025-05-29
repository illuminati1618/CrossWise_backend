from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from datetime import datetime
import traceback
from model.border_feedback import BorderFeedback
from __init__ import app, db

# Create Blueprint for Border Feedback API
border_feedback_api = Blueprint('border_feedback_api', __name__, url_prefix='/api/border_feedback')
api = Api(border_feedback_api)

class BorderFeedbackAPI:
    """
    Define the API endpoints for the BorderFeedback model.
    """
    class _Submit(Resource):
        def post(self):
            """
            Submit new border crossing feedback.
            """
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['time_cross', 'time_diff', 'time_taken']
                for field in required_fields:
                    if field not in data:
                        return {"error": f"Missing required field: {field}"}, 400
                
                # Parse and validate time_cross
                try:
                    time_cross = datetime.fromisoformat(data['time_cross'])
                except ValueError:
                    return {"error": "Invalid time_cross format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}, 400
                
                # Validate time_diff
                try:
                    time_diff = float(data['time_diff'])
                except ValueError:
                    return {"error": "time_diff must be a number"}, 400
                
                # Validate time_taken
                try:
                    time_taken = float(data['time_taken'])
                    if time_taken < 0:
                        return {"error": "time_taken cannot be negative"}, 400
                except ValueError:
                    return {"error": "time_taken must be a number"}, 400
                
                # Get optional user message
                user_message = data.get('user_message', '')
                
                # Create and save the feedback
                feedback = BorderFeedback(
                    time_cross=time_cross,
                    time_diff=time_diff,
                    time_taken=time_taken,
                    user_message=user_message
                )
                
                result = feedback.create()
                if result is None:
                    return {"error": "Failed to create feedback record"}, 500
                
                return {
                    "success": True,
                    "message": "Feedback submitted successfully",
                    "feedback_id": feedback.id
                }, 200
                
            except Exception as e:
                print(f"Error in border feedback submission: {str(e)}")
                print(traceback.format_exc())
                return {"error": str(e)}, 500
    
    class _GetRecent(Resource):
        def get(self):
            """
            Get recent feedback submissions.
            """
            try:
                limit = request.args.get('limit', 10, type=int)
                feedbacks = BorderFeedback.get_recent_feedback(limit)
                
                return {
                    "success": True,
                    "count": len(feedbacks),
                    "feedbacks": feedbacks
                }, 200
                
            except Exception as e:
                print(f"Error getting recent feedback: {str(e)}")
                print(traceback.format_exc())
                return {"error": str(e)}, 500
    
    # Register the resources with the API
    api.add_resource(_Submit, '/submit')
    api.add_resource(_GetRecent, '/recent')