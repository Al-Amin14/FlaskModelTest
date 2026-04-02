from flask import Blueprint,request,jsonify
from Controller.aisugController import get_course_suggestions

aisug=Blueprint('aisub',__name__)


# @aisug.route("/aisug",methods=["GET"])
# def get_patientvalue():
#     data=getpatientvalue()
#     return jsonify(data.tolist())



import jwt
import os
from functools import wraps
from flask import request, jsonify

SECRET_KEY = os.getenv("JWT_KEY")

# -------- JWT Decorator --------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            token = auth_header.split(" ")[1] if " " in auth_header else None

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            # Extract student_id from JWT claims
            student_id = (
                decoded.get("nameid") or
                decoded.get("sub") or
                decoded.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier")
            )

            if not student_id:
                return jsonify({"error": "Student ID not found in token"}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(student_id, *args, **kwargs)
    return decorated


# -------- Route --------
@aisug.route('/suggest', methods=['POST'])
@token_required
def suggest(student_id):
    data = request.get_json(silent=True) or {}  # 👈 silent=True fixes this
    top_n = data.get('top_n', 10)

    result = get_course_suggestions(student_id, top_n=top_n)
    return jsonify(result), 200