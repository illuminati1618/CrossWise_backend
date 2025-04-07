from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor
import pandas as pd
import numpy as np
import json
import os

'''
Sunday = 6
Monday = 0
Tuesday = 1
Wednesday = 2
Thursday = 3
Friday = 4
Saturday = 5
'''

class BorderWaitTimeModel:
    _instance = None

    def __init__(self):
        self.model = None
        self.dt = None
        self.features = []
        self.target = 'pv_time_avg'  # predicting private vehicle wait time
        self._load_data()

    def _load_data(self):
        dataset_folder = "datasets"
        months_mapping = {
            "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
            "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
        }

        data_list = []

        for filename in os.listdir(dataset_folder):
            if filename.endswith(".json"):
                file_path = os.path.join(dataset_folder, filename)
                month_name = filename.split(".")[0].lower()

                if month_name in months_mapping:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        for entry in data['wait_times']:
                            entry['month'] = months_mapping[month_name]
                            data_list.append(entry)

        df = pd.DataFrame(data_list)
        print("Loaded columns:", df.columns.tolist())

        categorical_features = ['bwt_day', 'time_slot', 'month']
        for col in categorical_features:
            df[col] = df[col].astype('category')

        df.dropna(inplace=True)

        self.features = [col for col in df.columns if col != self.target]
        X = df[self.features]
        y = df[self.target]

        self.model = HistGradientBoostingRegressor()
        self.model.fit(X, y)

        self.dt = DecisionTreeRegressor()
        self.dt.fit(X, y)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, wait_data):
        wait_df = pd.DataFrame([wait_data])

        for col in ['bwt_day', 'time_slot', 'month']:
            wait_df[col] = pd.Series(wait_df[col], dtype='category')

        # fill missing columns (if any)
        for col in self.features:
            if col not in wait_df.columns:
                wait_df[col] = 0

        wait_df = wait_df[self.features]

        prediction = self.model.predict(wait_df)[0]
        prediction = max(0, prediction)

        return {'predicted_wait_time': prediction}

    def feature_importance(self):
        importances = self.dt.feature_importances
        return {feature: importance for feature, importance in zip(self.features, importances)}
