import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

class WeatherFormatter:
    def __init__(self, file_path="datasets/san_diego_weather.csv"):
        self.file_path = file_path
        self.data = self._load_data()
        self.model = self._train_model()

    def _load_data(self):
        try:
            df = pd.read_csv(self.file_path)
        except Exception as e:
            raise FileNotFoundError(f"Error loading CSV: {e}")

        # Convert Date_Time to datetime format
        df['Date_Time'] = pd.to_datetime(df['Date_Time'])
        df['Hour'] = df['Date_Time'].dt.floor('H')  # Round down to the nearest hour

        # Drop irrelevant columns
        df.drop(columns=['Location'], errors='ignore', inplace=True)

        # Ensure numeric conversion for weather data
        weather_columns = ['Temperature_C', 'Humidity_pct', 'Precipitation_mm', 'Wind_Speed_kmh']
        for col in weather_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.dropna(subset=weather_columns, inplace=True)

        # Aggregate by hour (averaging values when multiple exist)
        df = df.groupby('Hour', as_index=False)[weather_columns].mean()

        return df

    def _train_model(self):
        # Prepare data for training AI model to fill missing values
        X = np.array([(dt.hour + dt.timetuple().tm_yday * 24) for dt in self.data['Hour']]).reshape(-1, 1)
        y = self.data[['Temperature_C', 'Humidity_pct', 'Precipitation_mm', 'Wind_Speed_kmh']]
        
        model = LinearRegression()
        model.fit(X, y)
        return model

    def _calculate_weather_score(self, temp, humidity, precipitation, wind_speed):
        score = 0
        
        if 15 <= temp <= 30:
            score += 1  # Good temperature range
        if 30 <= humidity <= 70:
            score += 1  # Comfortable humidity range
        if precipitation < 5:
            score += 1  # Low precipitation
        if wind_speed < 30:
            score += 1  # Manageable wind speed
        
        return score

    def generate_weather_data(self, days=7):
        weather_data = {}
        start_date = datetime(2024, 1, 1)
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
                
                for hour in range(24):  # Generate data for each hour
                    date_time_hour = date_time + timedelta(hours=hour)
                    hour_data = self.data[self.data['Hour'] == date_time_hour]
                    
                    if not hour_data.empty:
                        row = hour_data.iloc[0]
                        weather_data[month][day_name][str(hour)] = self._calculate_weather_score(
                            row['Temperature_C'], row['Humidity_pct'], row['Precipitation_mm'], row['Wind_Speed_kmh']
                        )
                    else:
                        predicted_values = self.model.predict(np.array([[hour + date_time_hour.timetuple().tm_yday * 24]]))[0]
                        weather_data[month][day_name][str(hour)] = self._calculate_weather_score(
                            predicted_values[0], predicted_values[1], predicted_values[2], predicted_values[3]
                        )
        
        return weather_data

'''
Example usage:
formatter = WeatherFormatter()
weather_list = formatter.generate_weather_data()
print(weather_list)
'''
