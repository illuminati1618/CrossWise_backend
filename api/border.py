from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from model.border import BorderWaitTimeModel
from datetime import datetime
import math
import requests
import json as JSON

border_api = Blueprint('border_api', __name__, url_prefix='/api/border')
api = Api(border_api)

class BorderAPI:
    class _Predict(Resource):
        def post(self):
            data = request.get_json()

            '''
            Day Maps:
            Sunday - 6
            Monday - 0
            Tuesday - 1
            Wednesday - 2
            Thursday - 3
            Friday - 4
            Saturday - 5

            Time Slot Maps:
            1 AM - 1
            2 AM - 2
            3 AM - 3
            4 AM - 4
            5 AM - 5
            6 AM - 6
            7 AM - 7
            8 AM - 8
            9 AM - 9
            10 AM - 10
            11 AM - 11
            12 PM - 12
            1 PM - 13
            2 PM - 14
            3 PM - 15
            4 PM - 16
            5 PM - 17
            6 PM - 18
            7 PM - 19
            8 PM - 20
            9 PM - 21
            10 PM - 22
            11 PM - 23
            Midnight - 0
            '''
            
            values = {}

            if "mode" not in data:
                values["mode"] = "long_term"
            else:
                values["mode"] = data["mode"]

            if "day" not in data:
                day_map = {6: 6, 0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
                current_day = datetime.now().weekday()
                values["day"] = day_map[current_day]
            else:
                day_map = {6: 6, 0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
                values["day"] = day_map[data["day"]]
            

            if "time" not in data:
                current_hour = datetime.now().hour  # already in 24-hour format
                values["time"] = current_hour
            else:
                values["time"] = data["time"]

            if values["mode"] == "long_term":
                borderModel = BorderWaitTimeModel.get_instance()
                response = borderModel.predict({"bwt_day": values["day"], "time_slot": values["time"]})

                return jsonify({
                    "time": math.trunc((response["linear_model_prediction"] + response["tree_model_prediction"]) / 2),
                })
            else:
                response = requests.get("https://bwt.cbp.gov/api/bwtwaittimegraph/09250401/2025-05-27")
                if response.status_code == 200:
                    response = response.json()

                    t_str = str(values["time"])
                    t = int(t_str)

                    slots = response[0]["private_time_slots"]["private_slot"]
                    differences = []
                    weights = []
                    slots = response[0]["private_time_slots"]["private_slot"]
                    differences = []
                    weights = []

                    for hour_int, slot in enumerate(slots):
                        if abs(hour_int - t) > 3:
                            continue
                        today_str = slot["standard_lane_today_wait"]
                        avg_str = slot["standard_lane_average_wait"]
                        if not today_str.isdigit() or not avg_str.isdigit():
                            continue
                        today_wait = int(today_str)
                        avg_wait = int(avg_str)
                        diff = today_wait - avg_wait
                        dist = abs(hour_int - t)
                        weight = 1 / pow(dist + 1, 2)
                        differences.append(diff * weight)
                        weights.append(weight)
                    if weights:
                        weighted_diff = sum(differences) / sum(weights)
                    else:
                        weighted_diff = 0
                    base_avg_str = slots[t]["standard_lane_average_wait"]
                    base_avg = int(base_avg_str) if base_avg_str.isdigit() else 0
                    predicted_today = base_avg + weighted_diff



                    return jsonify({
                        "time": str(math.trunc(predicted_today)),
                    })
                else:
                    return jsonify({"error": "Failed to fetch data from external API"}), 500

    api.add_resource(_Predict, '/predict')
