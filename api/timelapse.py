from flask import Blueprint, request, jsonify, send_file
from flask_restful import Api, Resource
from moviepy import *
from model.timelapse import TimelapseModel

timelapse_api = Blueprint('timelapse_api', __name__, url_prefix='/api/timelapse')
api = Api(timelapse_api)

class TimelapseAPI:
    class _Generate(Resource):
        def post(self):
            data = request.get_json()
            video_urls = data.get("videos", [])

            if not video_urls:
                return {"error": "No videos provided"}, 400

            try:
                output_path = TimelapseModel.generate(video_urls)
                return send_file(output_path, download_name="timelapse.mp4", mimetype="video/mp4")
            except Exception as e:
                return {"error": str(e)}, 500

    api.add_resource(_Generate, '/')