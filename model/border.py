from sklearn.linear_model import LinearRegression
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
        self._load_data()

    def _load_data(self):
        # Load all JSON files from the datasets directory
        data_dir = "datasets"
        all_data = []
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                with open(os.path.join(data_dir, filename), 'r') as f:
                    content = json.load(f)
                    all_data.extend(content["wait_times"])

        df = pd.DataFrame(all_data)
        df = df[self.features + [self.target]]
        df.dropna(inplace=True)

        # Convert features to integer
        df['bwt_day'] = df['bwt_day'].astype(int)
        df['time_slot'] = df['time_slot'].astype(int)
        df[self.target] = df[self.target].astype(float)

        X = df[self.features]
        y = df[self.target]

        self.model = LinearRegression()
        self.model.fit(X, y)

        self.dt = DecisionTreeRegressor()
        self.dt.fit(X, y)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, input_data):
        df = pd.DataFrame([input_data])
        df['bwt_day'] = df['bwt_day'].astype(int)
        df['time_slot'] = df['time_slot'].astype(int)

        linear_pred = float(self.model.predict(df)[0])
        tree_pred = float(self.dt.predict(df)[0])
        return {'linear_model_prediction': linear_pred, 'tree_model_prediction': tree_pred}

    def feature_importance(self):
        importances = self.dt.feature_importances_
        return {feature: importance for feature, importance in zip(self.features, importances)}
