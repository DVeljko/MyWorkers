from flask import Flask, jsonify, request
from models import db, Employee
from datetime import date
import requests
import os
from dotenv import load_dotenv

load_dotenv()
DEPARTMENT_SERVICE_URL = os.getenv("DEPARTMENT_SERVICE_URL")

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///employees.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def validate_department(department_id):
    try:
        response = requests.get(
            f"{DEPARTMENT_SERVICE_URL}/departments/{department_id}",
            timeout=3
        )

    except requests.exceptions.RequestException:
        return jsonify({"error": "Department service is unavailable"}), 503

    if response.status_code == 404:
        return jsonify({"error": "Department does not exist"}), 400

    return None


@app.route('/employees', methods=['GET'])
def get_all_employees():
    employees = db.session.scalars(db.select(Employee)).all()
    employees_list = [employee.to_dict() for employee in employees]
    return jsonify(employees_list)

@app.route("/employees/<int:department_id>", methods=['GET'])
def show_employees_by_department(department_id):
    error = validate_department(department_id)
    if error:
        return error

    employees_by_department = db.session.scalars(db.select(Employee).where(Employee.department_id == department_id))
    employees = [employee.to_dict() for employee in employees_by_department]
    return jsonify(employees)
    

@app.route("/employees/<int:employee_id>", methods=['GET'])
def single_employee(employee_id):
    employee = db.get_or_404(Employee, employee_id)
    return jsonify(employee.to_dict())

@app.route("/employees", methods=['POST'])
def add_employee():
    employee = request.get_json()
    department_id = employee["department_id"]

    error = validate_department(department_id=department_id)
    if error:
        return error
    
    new_employee = Employee(
        first_name = employee['first_name'],
        last_name = employee['last_name'],
        email = employee['email'],
        phone = employee['phone'],
        position = employee['position'],
        hire_date = date.fromisoformat(employee['hire_date']),
        salary = employee['salary'],
        status = employee['status'],
        department_id = employee['department_id']
    )

    db.session.add(new_employee)
    db.session.commit()
    return jsonify(new_employee.to_dict()), 201

@app.route("/employees/<int:employee_id>", methods=['PATCH'])
def update_employee(employee_id):
    employee = db.get_or_404(Employee, employee_id)
    data = request.get_json()

    if "department_id" in data:
        department_id = data['department_id']
        error = validate_department(department_id=department_id)

        if error:
            return error
        
    allowed_fields = ['phone', "position", "salary", "status", "department_id"]
    for field in allowed_fields:
        if field in data:
            setattr(employee, field, data[field])

    db.session.commit()

    return jsonify(employee.to_dict())


@app.route("/employee/<int:employee_id>", methods=['DELETE'])
def delete_employee(employee_id):
    employee = db.get_or_404(Employee, employee_id)
    db.session.delete(employee)
    db.session.commit()
    return jsonify({"message": "Employee deleted successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5002)