from flask import Blueprint, request, jsonify, send_file
from flask_restful import Api, Resource
from moviepy import *
from model.timelapse import TimelapseModel
from flask import Response
import requests

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

    @timelapse_api.route('/proxy_video')
    def proxy_video():
        url = request.args.get('url')
        if not url or not url.startswith("https://www.bordertraffic.com"):
            return {"error": "Invalid or unauthorized URL"}, 400

        try:
            resp = requests.get(url, stream=True, timeout=10)
            return Response(resp.iter_content(8192), content_type=resp.headers.get("Content-Type", "video/mp4"))
        except Exception as e:
            return {"error": str(e)}, 500