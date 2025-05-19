from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from model.weather_formater import WeatherFormatter
from datetime import datetime

# Create blueprint
weather_api = Blueprint('weather_api', __name__, url_prefix='/api')
api = Api(weather_api)

# Load formatter and data once to optimize
formatter = WeatherFormatter()

class WeatherAPI(Resource):
    def post(self):
        try:
            body = request.get_json()
            if not body or 'mode' not in body:
                return {"message": "Missing 'mode' in request body."}, 400

            mode = body.get('mode')

            if mode == 'datetime':
                date_str = body.get('datetime')
                if not date_str:
                    return {"message": "Missing 'datetime' in request body."}, 400

                try:
                    dt = datetime.fromisoformat(date_str)
                except ValueError:
                    return {"message": "Invalid datetime format. Use ISO format like '2024-03-25T14:00'"}, 400

                dt = dt.replace(minute=0, second=0, microsecond=0)
                prediction = formatter.get_weather_score_for_datetime(dt)
                return jsonify({
                    "datetime": dt.isoformat(),
                    "precipitation_mm": round(prediction['Precipitation'], 2),
                    "avg_temp_c": round(prediction['AvgTemp'], 2),
                    "min_temp_c": round(prediction['MinTemp'], 2),
                    "max_temp_c": round(prediction['MaxTemp'], 2)
                })

            elif mode == 'all':
                return {"message": "Mode 'all' is not supported with this model."}, 400

            elif mode == 'realtime':
                now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
                prediction = formatter.get_weather_score_for_datetime(now)
                return jsonify({
                    "datetime": now.isoformat(),
                    "precipitation_mm": round(prediction['Precipitation'], 2),
                    "avg_temp_c": round(prediction['AvgTemp'], 2),
                    "min_temp_c": round(prediction['MinTemp'], 2),
                    "max_temp_c": round(prediction['MaxTemp'], 2)
                })

            else:
                return {"message": "Invalid mode. Use 'datetime' or 'realtime'."}, 400

        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500

api.add_resource(WeatherAPI, '/weather-data')
