import jwt
from flask import Blueprint, request, jsonify, current_app, Response
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

            # Check if face encoding already exists for this user
            existing_face = FaceEncoding.query.filter_by(uid=uid).first()
            if existing_face:
                # Update existing encoding
                existing_face.encoding_array = encoding
            else:
                # Create new encoding
                face_entry = FaceEncoding(uid=uid, encoding_array=encoding)
                db.session.add(face_entry)
            
            db.session.commit()

            return {"message": f"Face registered for {uid}", "success": True}, 200

    class _RecognizeFace(Resource):
        def post(self):
            try:
                data = request.get_json()
                image_data = data.get('image')
                if not image_data:
                    return {"message": "Missing image data"}, 400

                encoding = get_face_encodings_from_image(image_data)
                if encoding is None:
                    return {"message": "No face detected"}, 400

                known_faces = FaceEncoding.query.all()
                recognized_user = None
                
                for face in known_faces:
                    known_encoding = face.decode_face()
                    matches = face_recognition.compare_faces([known_encoding], encoding, tolerance=0.6)
                    if matches[0]:
                        # Face recognized, now get the user
                        user = User.query.filter_by(_uid=face.uid).first()
                        if user:
                            recognized_user = user
                            break

                if not recognized_user:
                    return {"message": "Face not recognized"}, 404

                # Generate JWT token (same as regular login)
                token = jwt.encode(
                    {"_uid": recognized_user._uid},
                    current_app.config["SECRET_KEY"],
                    algorithm="HS256"
                )
                
                # Create response with JWT token in cookie (same as regular login)
                resp = Response(jsonify({
                    "message": "Face recognized and authenticated successfully",
                    "username": recognized_user._uid,
                    "success": True
                }).data, content_type='application/json')
                
                resp.set_cookie(
                    current_app.config["JWT_TOKEN_NAME"],
                    token,
                    max_age=3600,
                    secure=True,
                    httponly=True,
                    path='/',
                    samesite='None'  # This is the key part for cross-site requests
                )
                
                return resp

            except Exception as e:
                print(f"Error in facial recognition: {str(e)}")
                return {"message": "Internal server error during facial recognition", "error": str(e)}, 500

    api.add_resource(_RegisterFace, '/register')
    api.add_resource(_RecognizeFace, '/recognize')