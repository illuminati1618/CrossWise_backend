import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

class WeatherModel:
    _instance = None

    def __init__(self):
        self.model = None
        self.features = ['Date', 'Time']  # Using Date and Time as features
        self.target = ['Temperature_C', 'Humidity_pct', 'Precipitation_mm', 'Wind_Speed_kmh']
        self._load_data()

    def _load_data(self):
        file_path = "datasets/san_diego_weather.csv"
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise FileNotFoundError(f"Error loading CSV: {e}")

        # Convert Date_Time to datetime and extract the date and time
        df['Date'] = pd.to_datetime(df['Date_Time']).dt.date
        df['Time'] = pd.to_datetime(df['Date_Time']).dt.time

        # Convert the reference_date to datetime.date (matching the type of df['Date'])
        reference_date = datetime(2000, 1, 1).date()
        df['Date'] = df['Date'].apply(lambda x: (x - reference_date).days)

        # Convert time to the number of seconds since midnight
        df['Time'] = df['Time'].apply(lambda x: x.hour * 3600 + x.minute * 60 + x.second)

        # Drop irrelevant columns like 'Location' and 'Date_Time'
        df.drop(columns=['Location', 'Date_Time'], errors='ignore', inplace=True)

        # Ensure all required columns are present
        missing_cols = set(self.features + self.target) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing columns in dataset: {missing_cols}")

        # Check for non-numeric values in target columns
        for target in self.target:
            df[target] = pd.to_numeric(df[target], errors='coerce')
        df.dropna(subset=self.target, inplace=True)

        # Prepare data for training
        X = df[self.features]
        y = df[self.target]

        if X.empty:
            raise ValueError("Dataset is empty after preprocessing! Check the CSV file.")

        # Train the model
        self.model = LinearRegression()
        self.model.fit(X, y)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, datetime_str):
        input_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        reference_date = datetime(2000, 1, 1).date()
        date_diff = (input_datetime.date() - reference_date).days
        time_in_seconds = input_datetime.hour * 3600 + input_datetime.minute * 60 + input_datetime.second

        weather_data_transformed = pd.DataFrame([[date_diff, time_in_seconds]], columns=self.features)
        predicted_values = self.model.predict(weather_data_transformed)[0]
        prediction_dict = {self.target[i]: predicted_values[i] for i in range(len(self.target))}
        
        # Get the final weather classification
        prediction_dict['Overall_Weather_Classification'] = self.classify_weather(prediction_dict)
        
        return prediction_dict

    def classify_weather(self, weather_data):
        temp = weather_data['Temperature_C']
        humidity = weather_data['Humidity_pct']
        precipitation = weather_data['Precipitation_mm']
        wind_speed = weather_data['Wind_Speed_kmh']

        score = 0
        
        if 15 <= temp <= 30:
            score += 1  # Good temperature range
        if 30 <= humidity <= 70:
            score += 1  # Comfortable humidity range
        if precipitation < 5:
            score += 1  # Low precipitation
        if wind_speed < 30:
            score += 1  # Manageable wind speed
        
        if score == 4:
            return "Excellent"
        elif score == 3:
            return "Good"
        elif score == 2:
            return "Moderate"
        else:
            return "Bad"

    def generate_weather_data(self, days=7):
        weather_data = {}
        start_date = datetime(2025, 1, 1)
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        
        for month_index, month in enumerate(months):
            month_start_date = start_date + timedelta(days=month_index * 30)  # Approximate start of each month
            weather_data[month] = {}
            
            for day in range(days):
                date_time = month_start_date + timedelta(days=day)
                day_name = date_time.strftime('%A')
                weather_data[month][day_name] = {}
                
                for hour in range(24):  # Generate predictions for each hour
                    date_time_hour = date_time + timedelta(hours=hour)
                    prediction = self.predict(date_time_hour.strftime('%Y-%m-%d %H:%M:%S'))
                    weather_data[month][day_name][str(hour)] = prediction['Overall_Weather_Classification']
        
        return weather_data

# Example usage:
model = WeatherModel.get_instance()
weather_list = model.generate_weather_data()
print(weather_list)
