from flask import Blueprint ,request, jsonify
from Controller.user_controller import get_all_user,create_user

user_bp=Blueprint("user_bp",__name__)

@user_bp.route("/",methods=["GET"])
def get_users():
    return jsonify(get_all_user())

@user_bp.route("/",methods=["POST"])
def app_user():
    data=request.get_json()
    return jsonify(create_user(data),201)