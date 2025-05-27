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
        raw_periods = resp.json()["properties"]["periods"]

        forecast = []
        for period in raw_periods:
            temp = period.get("temperature")
            is_daytime = period.get("isDaytime", True)
            start_time = period.get("startTime")
            name = period.get("name")
            forecast_text = period.get("shortForecast", "N/A")
            precip = period.get("probabilityOfPrecipitation", {}).get("value", 0) or 0

            # Convert to ISO date
            date_obj = datetime.fromisoformat(start_time)
            date_key = date_obj.strftime('%Y-%m-%d')

            # Check if the entry for the date already exists
            existing = next((f for f in forecast if f["date"] == date_key), None)

            if existing:
                if is_daytime and temp > existing["high_f"]:
                    existing["high_f"] = temp
                if not is_daytime and temp < existing["low_f"]:
                    existing["low_f"] = temp
                existing["temps"].append(temp)
                existing["precip"].append(precip)
            else:
                forecast.append({
                    "name": name,
                    "startTime": start_time,
                    "date": date_key,
                    "short_forecast": forecast_text,
                    "high_f": temp if is_daytime else float('-inf'),
                    "low_f": temp if not is_daytime else float('inf'),
                    "temps": [temp],
                    "precip": [precip],
                    "isDaytime": is_daytime
                })

        # Finalize entries
        for entry in forecast:
            entry["temperature_f"] = round(sum(entry["temps"]) / len(entry["temps"]))
            entry["precip_chance"] = round(sum(entry["precip"]) / len(entry["precip"]))
            if entry["low_f"] == float('inf'):
                entry["low_f"] = entry["temperature_f"]
            if entry["high_f"] == float('-inf'):
                entry["high_f"] = entry["temperature_f"]
            del entry["temps"]
            del entry["precip"]

        return forecast

    def get_current_forecast(self):
        periods = self.get_weekly_forecast()
        now = datetime.utcnow().date()
        for p in periods:
            forecast_date = datetime.fromisoformat(p["startTime"]).date()
            if forecast_date == now:
                return p
        return periods[0]
