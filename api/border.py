from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from model.border import BorderWaitTimeModel

border_api = Blueprint('border_api', __name__, url_prefix='/api/border')
api = Api(border_api)

class BorderAPI:
    class _Predict(Resource):
        def post(self):
            data = request.get_json()
            '''
            required_fields = ['bwt_day', 'time_slot', 'month', 'weather_score']

            if not all(field in data for field in required_fields):
                return {"error": "Missing required fields", "required_fields": required_fields}, 400
            '''

            borderModel = BorderWaitTimeModel.get_instance()
            response = borderModel.predict({"bwt_day": 2, "time_slot": 15})

            return jsonify(response)

    api.add_resource(_Predict, '/predict')
