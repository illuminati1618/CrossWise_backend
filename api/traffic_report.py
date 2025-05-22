from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from datetime import datetime
import traceback
from model.traffic_report import TrafficReport
from __init__ import app, db

# Create Blueprint for Traffic Report API
traffic_report_api = Blueprint('traffic_report_api', __name__, url_prefix='/api/traffic_report')
api = Api(traffic_report_api)

class TrafficReportAPI:
    """
    Define the API endpoints for the TrafficReport model.
    """
    class _Submit(Resource):
        def post(self):
            """
            Submit new traffic/accident report.
            """
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ['report_time', 'reason', 'border_location', 'direction']
                for field in required_fields:
                    if field not in data:
                        return {"error": f"Missing required field: {field}"}, 400
                
                # Parse and validate report_time
                try:
                    report_time = datetime.fromisoformat(data['report_time'])
                except ValueError:
                    return {"error": "Invalid report_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}, 400
                
                # Validate reason
                valid_reasons = ['traffic', 'accident', 'natural disaster', 'road construction', 'police checkpoint', 'road closure']
                if data['reason'] not in valid_reasons:
                    return {"error": f"Invalid reason. Must be one of: {', '.join(valid_reasons)}"}, 400
                
                # Validate border location
                valid_locations = ['San Ysidro', 'Otay Mesa']
                if data['border_location'] not in valid_locations:
                    return {"error": f"Invalid border location. Must be one of: {', '.join(valid_locations)}"}, 400
                
                # Validate direction
                valid_directions = ['entering us', 'entering mexico']
                if data['direction'] not in valid_directions:
                    return {"error": f"Invalid direction. Must be one of: {', '.join(valid_directions)}"}, 400
                
                # Get optional comments
                comments = data.get('comments', '')
                
                # Create and save the traffic report
                traffic_report = TrafficReport(
                    report_time=report_time,
                    reason=data['reason'],
                    border_location=data['border_location'],
                    direction=data['direction'],
                    comments=comments
                )
                
                result = traffic_report.create()
                if result is None:
                    return {"error": "Failed to create traffic report"}, 500
                
                return {
                    "success": True,
                    "message": "Traffic report submitted successfully",
                    "report_id": traffic_report.id
                }, 200
                
            except Exception as e:
                print(f"Error in traffic report submission: {str(e)}")
                print(traceback.format_exc())
                return {"error": str(e)}, 500
    
    class _GetRecent(Resource):
        def get(self):
            """
            Get recent traffic reports.
            """
            try:
                limit = request.args.get('limit', 10, type=int)
                reports = TrafficReport.get_recent_reports(limit)
                
                return {
                    "success": True,
                    "count": len(reports),
                    "reports": reports
                }, 200
                
            except Exception as e:
                print(f"Error getting recent traffic reports: {str(e)}")
                print(traceback.format_exc())
                return {"error": str(e)}, 500
    
    class _GetByLocation(Resource):
        def post(self):
            """
            Get traffic reports by border location.
            """
            try:
                data = request.get_json()
                
                if 'border_location' not in data:
                    return {"error": "Missing border_location field"}, 400
                
                limit = data.get('limit', 20)
                reports = TrafficReport.get_reports_by_location(data['border_location'], limit)
                
                return {
                    "success": True,
                    "border_location": data['border_location'],
                    "count": len(reports),
                    "reports": reports
                }, 200
                
            except Exception as e:
                print(f"Error getting traffic reports by location: {str(e)}")
                print(traceback.format_exc())
                return {"error": str(e)}, 500
    
    # Register the resources with the API
    api.add_resource(_Submit, '/submit')
    api.add_resource(_GetRecent, '/recent')
    api.add_resource(_GetByLocation, '/location')