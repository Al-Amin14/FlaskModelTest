from flask import Blueprint,request,jsonify
from Controller.aisugController import get_course_suggestions

aisug=Blueprint('aisub',__name__)


# @aisug.route("/aisug",methods=["GET"])
# def get_patientvalue():
#     data=getpatientvalue()
#     return jsonify(data.tolist())

@aisug.route('/suggest', methods=['POST'])
def suggest():
    data = request.get_json()
    student_id = data.get('student_id')
    top_n = data.get('top_n', 10)  # default 10 suggestions

    if not student_id:
        return jsonify({"error": "student_id is required"}), 400

    result = get_course_suggestions(student_id, top_n=top_n)
    return jsonify(result), 200
