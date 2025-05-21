from flask import Blueprint, jsonify
from flask_restful import Api, Resource
from model.weather_formater import NOAAWeatherFetcher

weather_api = Blueprint('weather_api', __name__, url_prefix='/api')
api = Api(weather_api)
fetcher = NOAAWeatherFetcher()

class RealtimeWeather(Resource):
    def get(self):
        try:
            forecast = fetcher.get_current_forecast()
            return jsonify({
                "datetime": forecast["startTime"],
                "temperature_f": forecast["temperature"],
                "short_forecast": forecast["shortForecast"],
                "precip_chance": forecast.get("probabilityOfPrecipitation", {}).get("value", 0)
            })
        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500

class WeeklyForecast(Resource):
    def get(self):
        try:
            periods = fetcher.get_weekly_forecast()
            result = [{
                "name": p["name"],
                "startTime": p["startTime"],
                "temperature_f": p["temperature"],
                "short_forecast": p["shortForecast"],
                "precip_chance": p.get("probabilityOfPrecipitation", {}).get("value", 0)
            } for p in periods if p["isDaytime"]]
            return jsonify(result)
        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500

api.add_resource(RealtimeWeather, '/weather-now')
api.add_resource(WeeklyForecast, '/forecast-week')
