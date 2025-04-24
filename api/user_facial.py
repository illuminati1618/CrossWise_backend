from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from model.facial_encoding import FaceEncoding
from model.user import User
from __init__ import db
import face_recognition
import numpy as np
import base64
import io
from PIL import Image

def get_face_encodings_from_image(base64_str):
    try:
        img_bytes = base64.b64decode(base64_str)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        np_img = np.array(img)
        encodings = face_recognition.face_encodings(np_img)
        return encodings[0] if encodings else None
    except Exception as e:
        print("Encoding Error:", e)
        return None

facial_api = Blueprint('facial_api', __name__, url_prefix='/user/facial')
api = Api(facial_api)

class FacialAPI:
        class _RegisterFace(Resource):
            def post(self):
                data = request.get_json()
                image_data = data.get('image')
                uid = data.get('uid')

                if not image_data or not uid:
                    return {"message": "Missing image or uid"}, 400

                user = User.query.filter_by(_uid=uid).first()
                if not user:
                    return {"message": "User not found"}, 404

                encoding = get_face_encodings_from_image(image_data)
                if encoding is None:
                    return {"message": "No face detected"}, 400

                face_entry = FaceEncoding(uid=uid, encoding_array=encoding)
                db.session.add(face_entry)
                db.session.commit()

                return {"message": f"Face registered for {uid}"}, 200

        class _RecognizeFace(Resource):
            def post(self):
                data = request.get_json()
                image_data = data.get('image')
                if not image_data:
                    return {"message": "Missing image data"}, 400

                encoding = get_face_encodings_from_image(image_data)
                if encoding is None:
                    return {"message": "No face detected"}, 400

                known_faces = FaceEncoding.query.all()
                for face in known_faces:
                    known_encoding = face.decode_face()
                    matches = face_recognition.compare_faces([known_encoding], encoding)
                    if matches[0]:
                        return {"message": "Face recognized", "username": face.uid}, 200

                return {"message": "Face not recognized"}, 404

        api.add_resource(_RegisterFace, '/register')
        api.add_resource(_RecognizeFace, '/recognize')
