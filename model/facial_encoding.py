from __init__ import db
import numpy as np
import json

class FaceEncoding(db.Model):
    __tablename__ = 'face_encodings'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), db.ForeignKey('users._uid'), unique=True, nullable=False)
    encoding = db.Column(db.Text, nullable=False)

    def __init__(self, uid, encoding_array):
        self.uid = uid
        self.encoding = json.dumps(encoding_array.tolist())

    def decode_face(self):
        return np.array(json.loads(self.encoding))


class FacialEncoding5c(db.Model):
    __tablename__ = 'facial_encodings_5c'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), db.ForeignKey('users._uid'), unique=True, nullable=False)
    encoding = db.Column(db.Text, nullable=False)

    def __init__(self, uid, encoding_array):
        self.uid = uid
        self.encoding = json.dumps(encoding_array.tolist())

    def decode_face(self):
        return np.array(json.loads(self.encoding))
