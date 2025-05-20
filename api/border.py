from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from model.border import BorderWaitTimeModel
from datetime import datetime
import math

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


            print(f"Day: {values['day']}, Time: {values['time']}")

            borderModel = BorderWaitTimeModel.get_instance()
            response = borderModel.predict({"bwt_day": values["day"], "time_slot": values["time"]})

            return jsonify({
                "time": math.trunc((response["linear_model_prediction"] + response["tree_model_prediction"]) / 2),
            })

    api.add_resource(_Predict, '/predict')
