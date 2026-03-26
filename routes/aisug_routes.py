from flask import Blueprint,request,jsonify
from Controller.aisugController import getpatientvalue

aisug=Blueprint('aisub',__name__)


@aisug.route("/aisug",methods=["GET"])
def get_patientvalue():
    data=getpatientvalue()
    return jsonify(data.tolist())