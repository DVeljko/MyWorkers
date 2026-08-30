from flask import Flask, jsonify
from models import Attendance, db
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

EMPLOYEE_SERVICE_URL = os.getenv('EMPLOYEE_SERVICE_URL')

def validate_employee(employee_id):
    try:
        response = requests.get(
            f"{EMPLOYEE_SERVICE_URL}/employees/{employee_id}",
            timeout=3
        )

    except requests.exceptions.RequestException:
        return jsonify({"error": "Employee service is unavailable"})

    if response.status_code == 404:
        return jsonify({"error": "Employee does not exist"})

    return None

if __name__ == "__main__":
    app.run(debug=True, port=5003)