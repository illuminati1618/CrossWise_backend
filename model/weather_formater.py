import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from datetime import datetime

class WeatherFormatter:
    def __init__(self, file_path="datasets/san_diego_weather.csv"):
        self.file_path = file_path
        self.data = self._load_data()
        self.model = self._train_model()

    def _load_data(self):
        df = pd.read_csv(self.file_path)
        df['DATE'] = pd.to_datetime(df['DATE'])
        df['Month'] = df['DATE'].dt.month
        df['DayOfYear'] = df['DATE'].dt.dayofyear
        df['DayOfWeek'] = df['DATE'].dt.weekday

        df['PRCP'] = df['PRCP'].fillna(0)
        df = df.ffill()

        return df

    def _train_model(self):
        X = self.data[['Month', 'DayOfYear', 'DayOfWeek']]
        y = self.data[['PRCP', 'TAVG', 'TMIN', 'TMAX']]  # Multi-output

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)

        return model

    def predict(self, input_data):
        input_df = pd.DataFrame([input_data])
        prediction = self.model.predict(input_df)[0]

        return {
            'Precipitation': float(prediction[0]),
            'AvgTemp': float(prediction[1]),
            'MinTemp': float(prediction[2]),
            'MaxTemp': float(prediction[3]),
        }


    def get_weather_score_for_datetime(self, dt):
        input_data = {
            'Month': dt.month,
            'DayOfYear': dt.timetuple().tm_yday,
            'DayOfWeek': dt.weekday(),
        }
        return self.predict(input_data)

# Example usage
weather = WeatherFormatter(file_path="datasets/san_diego_weather.csv")

result = weather.get_weather_score_for_datetime(datetime(2025, 5, 19))
print(result)
