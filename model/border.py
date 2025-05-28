from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import OneHotEncoder
import pandas as pd
import numpy as np
import os
import json

class BorderWaitTimeModel:
    _instance = None

    def __init__(self):
        self.model = None
        self.dt = None
        self.features = ['bwt_day', 'time_slot']
        self.target = 'pv_time_avg'
        self.encoder = OneHotEncoder(handle_unknown='ignore')

    def _load_data(self, month):
        # Load the JSON file for the specified month
        data_dir = "datasets"
        file_path = os.path.join(data_dir, f"{month}.json")
                
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No dataset found for month: {month}")

        with open(file_path, 'r') as f:
            content = json.load(f)

        all_data = content.get("wait_times", [])

        df = pd.DataFrame(all_data)
        df = df[self.features + [self.target]]
        df.dropna(inplace=True)

        # Convert features to integer
        df['bwt_day'] = df['bwt_day'].astype(int)
        df['time_slot'] = df['time_slot'].astype(int)
        df[self.target] = df[self.target].astype(float)

        X = df[self.features]
        y = df[self.target]

        self.model = RandomForestRegressor(random_state=42, n_estimators=100)
        self.model.fit(X, y)

        self.dt = DecisionTreeRegressor()
        self.dt.fit(X, y)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, input_data):
        month = input_data.get('month')
        if month is None:
            raise ValueError("Month must be provided in the input data.")

        self._load_data(month)

        df = pd.DataFrame([input_data])
        df['bwt_day'] = df['bwt_day'].astype(int)
        df['time_slot'] = df['time_slot'].astype(int)

        rf_pred = float(self.model.predict(df[self.features])[0])
        tree_pred = float(self.dt.predict(df[self.features])[0])
        return {'random_forest_prediction': rf_pred, 'tree_model_prediction': tree_pred}

    def feature_importance(self):
        importances = self.model.feature_importances_
        return {feature: importance for feature, importance in zip(self.features, importances)}
