from flask import Blueprint, jsonify
from flask_restful import Api, Resource
from model.weather_formater import NOAAWeatherFetcher

# Define Blueprint and API
weather_api = Blueprint('weather_api', __name__, url_prefix='/api')
api = Api(weather_api)

# Weather data fetcher instance
fetcher = NOAAWeatherFetcher()

# Realtime weather endpoint
class RealtimeWeather(Resource):
    def get(self):
        try:
            forecast = fetcher.get_current_forecast()
            return jsonify({
                "date": forecast["date"],
                "datetime": forecast["startTime"],
                "temperature_f": forecast["temperature_f"],
                "high_f": forecast["high_f"],
                "low_f": forecast["low_f"],
                "short_forecast": forecast["short_forecast"],
                "precip_chance": forecast["precip_chance"]
            })
        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500

# Weekly forecast endpoint
class WeeklyForecast(Resource):
    def get(self):
        try:
            periods = fetcher.get_weekly_forecast()
            result = []
            for p in periods:
                result.append({
                    "name": p["name"],
                    "startTime": p["startTime"],
                    "temperature_f": p["temperature_f"],
                    "high_f": p["high_f"],
                    "low_f": p["low_f"],
                    "avg_f": p["temperature_f"],
                    "short_forecast": p["short_forecast"],
                    "precip_chance": p["precip_chance"],
                    "isDaytime": p["isDaytime"]
                })
            return jsonify(result)
        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500

# Register resources with the API
api.add_resource(RealtimeWeather, '/weather-now')
api.add_resource(WeeklyForecast, '/forecast-week')
