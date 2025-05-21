import requests
from datetime import datetime

class NOAAWeatherFetcher:
    def __init__(self, lat=32.7157, lon=-117.1611):
        self.lat = lat
        self.lon = lon
        self.gridpoint_url = self._get_gridpoint_url()

    def _get_gridpoint_url(self):
        url = f"https://api.weather.gov/points/{self.lat},{self.lon}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()["properties"]["forecast"]

    def get_weekly_forecast(self):
        resp = requests.get(self.gridpoint_url, timeout=10)
        resp.raise_for_status()
        return resp.json()["properties"]["periods"]

    def get_current_forecast(self):
        periods = self.get_weekly_forecast()
        now = datetime.utcnow()
        for p in periods:
            start = datetime.fromisoformat(p["startTime"])
            if start.date() == now.date():
                return p
        return periods[0]
