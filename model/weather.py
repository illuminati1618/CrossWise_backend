import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime

class WeatherModel:
    _instance = None

    def __init__(self):
        self.model = None
        self.features = ['Date', 'Time']  # Using Date and Time as features
        self.target = ['Temperature_C', 'Humidity_pct', 'Precipitation_mm', 'Wind_Speed_kmh']
        self._load_data()

    def _load_data(self):
        file_path = "datasets/san_diego_weather.csv"
        # print("Loading dataset...")

        try:
            df = pd.read_csv(file_path)
            # print(df.head())  # Check first few rows
        except Exception as e:
            raise FileNotFoundError(f"Error loading CSV: {e}")

        # Convert Date_Time to datetime and extract the date and time
        df['Date'] = pd.to_datetime(df['Date_Time']).dt.date
        df['Time'] = pd.to_datetime(df['Date_Time']).dt.time

        # Convert the reference_date to datetime.date (matching the type of df['Date'])
        reference_date = datetime(2000, 1, 1).date()  # Ensure it's a date object
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
        # print("Model trained successfully.")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, datetime_str):
        # Convert input Date_Time string to datetime object
        input_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

        # Convert input date and time to numerical values
        reference_date = datetime(2000, 1, 1).date()  # Ensure it's a date object
        date_diff = (input_datetime.date() - reference_date).days
        time_in_seconds = input_datetime.hour * 3600 + input_datetime.minute * 60 + input_datetime.second

        # Create the transformed input for prediction
        weather_data_transformed = pd.DataFrame([[date_diff, time_in_seconds]], columns=self.features)
        # print("Prediction Input:", weather_data_transformed)

        # Get the predicted values for Temperature, Humidity, Precipitation, and Wind Speed
        predicted_values = self.model.predict(weather_data_transformed)[0]
        prediction_dict = {self.target[i]: predicted_values[i] for i in range(len(self.target))}

        # Print the predictions in a human-readable format
        print(f"\nPrediction Date and Time: {input_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
        print("Predicted Weather Information:")
        for key, value in prediction_dict.items():
            print(f"{key.replace('_', ' ').title()}: {value:.2f}")

        return prediction_dict


    def feature_weights(self):
        return {feature: weight for feature, weight in zip(self.features, self.model.coef_.flatten())}

# Example usage:
model = WeatherModel.get_instance()

# Predict based on date and time input
prediction = model.predict('2025-04-11 22:46:21')  # Date and Time in 'YYYY-MM-DD HH:MM:SS' format

#classifier

