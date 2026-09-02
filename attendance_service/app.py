from flask import Flask, jsonify, request
from models import Attendance, db
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
from flask_jwt_extended import JWTManager, jwt_required, get_jwt, get_jwt_identity

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

EMPLOYEE_SERVICE_URL = os.getenv('EMPLOYEE_SERVICE_URL')
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

def validate_employee(employee_id):
    token = request.headers.get("Authorization")

    try:
        response = requests.get(
            f"{EMPLOYEE_SERVICE_URL}/employees/{employee_id}",
            headers={
                "Authorization": token
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return jsonify({"error": "Employee service is unavailable"}), 503

    if response.status_code == 404:
        return jsonify({"error": "Employee does not exist"}), 400

    if response.status_code == 401:
        return jsonify({"error": "Unauthorized"}), 401

    if response.status_code == 403:
        return jsonify({"error": "Forbidden"}), 403

    return None


@app.route("/attendance/<int:employee_id>", methods=["POST"])
@jwt_required()
def check_in(employee_id):

    claims = get_jwt()

    if claims["role"] not in ["employee", "admin"]:
        return jsonify({"error": "Only admin or employee can check in"}), 403

    if claims["role"] == "employee" and claims["employee_id"] != employee_id:
        return jsonify({"error": "You can only check in yourself"}), 403

    error = validate_employee(employee_id)
    if error:
        return error

    active_attendance = db.session.scalar(
        db.select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.departure_time == None
        )
    )

    if active_attendance:
        return jsonify({"error": "Employee is already checked in"}), 409

    attendance = Attendance(
        employee_id=employee_id,
        arrival_time=datetime.now()
    )

    db.session.add(attendance)
    db.session.commit()

    return jsonify(attendance.to_dict()), 201


@app.route("/attendance/<int:employee_id>", methods=["PATCH"])
@jwt_required()
def check_out(employee_id):

    claims = get_jwt()

    if claims["role"] not in ["employee", "admin"]:
        return jsonify({"error": "Only admin or employee can check out"}), 403

    if claims["role"] == "employee" and claims["employee_id"] != employee_id:
        return jsonify({"error": "You can only check out yourself"}), 403

    error = validate_employee(employee_id)
    if error:
        return error

    attendance = db.session.scalar(
        db.select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.departure_time == None
        )
    )

    if attendance is None:
        return jsonify({"error": "Employee is not checked in"}), 409

    attendance.departure_time = datetime.now()
    db.session.commit()

    return jsonify(attendance.to_dict())


@app.route("/attendance", methods=["GET"])
@jwt_required()
def all_attendance():

    claims = get_jwt()

    if claims["role"] not in ["admin", "manager"]:
        return jsonify({"error": "Only admin or manager can see all attendance"}), 403

    attendances = db.session.scalars(
        db.select(Attendance)
    ).all()

    list_of_attendances = [
        attendance.to_dict()
        for attendance in attendances
    ]

    return jsonify(list_of_attendances)


@app.route("/attendance/<int:attendance_id>", methods=["GET"])
@jwt_required()
def get_attendance(attendance_id):

    claims = get_jwt()

    if claims["role"] not in ["admin", "manager"]:
        return jsonify({"error": "Only admin or manager can get attendance"}), 403

    attendance = db.get_or_404(Attendance, attendance_id)

    return jsonify(attendance.to_dict())

@app.route("/employee/<int:employee_id>/attendance", methods=["GET"])
@jwt_required()
def get_attendance_by_employee_id(employee_id):

    claims = get_jwt()

    if claims["role"] not in ["admin", "manager", "employee"]:
        return jsonify({
            "error": "Only admin, manager or employee can get attendance"
        }), 403

    if claims["role"] == "employee" and claims["employee_id"] != employee_id:
        return jsonify({
            "error": "You can only see your own attendance"
        }), 403

    error = validate_employee(employee_id)
    if error:
        return error

    attendances = db.session.scalars(
        db.select(Attendance).where(
            Attendance.employee_id == employee_id
        )
    ).all()

    if not attendances:
        return jsonify({
            "error": "There is no data for this employee"
        }), 404

    employee_attendance = [
        attendance.to_dict()
        for attendance in attendances
    ]

    return jsonify(employee_attendance)

@app.route("/attendance/<int:attendance_id>", methods=["DELETE"])
@jwt_required()
def delete_attendance(attendance_id):

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({
            "error": "Only admin can delete attendance of employee"
        }), 403

    attendance = db.get_or_404(Attendance, attendance_id)

    db.session.delete(attendance)
    db.session.commit()

    return jsonify({
        "message": "Attendance deleted successfully"
    })

if __name__ == "__main__":
    app.run(debug=True, port=5003)