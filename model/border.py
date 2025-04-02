from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import OneHotEncoder
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
        self.encoder = OneHotEncoder(handle_unknown='ignore')
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
                            entry['month'] = months_mapping[month_name]  # Assign month as integer
                            data_list.append(entry)
        
        df = pd.DataFrame(data_list)
        print("Loaded columns:", df.columns.tolist())

        categorical_features = ['bwt_day', 'time_slot', 'month']
        onehot = self.encoder.fit_transform(df[categorical_features]).toarray()
        cols = list(self.encoder.get_feature_names_out(categorical_features))
        onehot_df = pd.DataFrame(onehot, columns=cols)
        
        df = pd.concat([df.drop(columns=categorical_features), onehot_df], axis=1)
        df.dropna(inplace=True)
        
        self.features = [col for col in df.columns if col != self.target]
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
    
    def predict(self, wait_data):
        wait_df = pd.DataFrame([wait_data])

        onehot = self.encoder.transform(wait_df[['bwt_day', 'time_slot', 'month']]).toarray()
        cols = list(self.encoder.get_feature_names_out(['bwt_day', 'time_slot', 'month']))
        onehot_df = pd.DataFrame(onehot, columns=cols)

        wait_df = pd.concat([wait_df.drop(columns=['bwt_day', 'time_slot', 'month']), onehot_df], axis=1)

        for col in self.features:
            if col not in wait_df:
                wait_df[col] = 0
        wait_df = wait_df[self.features]

        prediction = self.model.predict(wait_df)[0]
        prediction = max(0, prediction)
        
        return {'predicted_wait_time': prediction}

    def feature_importance(self):
        importances = self.dt.feature_importances_
        return {feature: importance for feature, importance in zip(self.features, importances)}
