from flask import Flask, jsonify, request
from models import db, Employee
from datetime import date
import requests
import os
from sqlalchemy import or_
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, jwt_required, get_jwt, get_jwt_identity

load_dotenv()
DEPARTMENT_SERVICE_URL = os.getenv("DEPARTMENT_SERVICE_URL")

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///employees.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
jwt = JWTManager(app)

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
@jwt_required()
def get_all_employees():

    claims = get_jwt()
    if claims['role'] not in ['admin','manager']:
        return jsonify({"error":"Only admin or manager can see all employees"}), 403
    
    name = request.args.get('name')
    if name:
        employee = db.session.scalars(db.select(Employee).where(or_(Employee.first_name.ilike(f"%{name}%"), Employee.last_name.ilike(f"%{name}%")))).all()
        employee_list = [emp.to_dict() for emp in employee]
        return jsonify(employee_list)

    employees = db.session.scalars(db.select(Employee)).all()
    employees_list = [employee.to_dict() for employee in employees]
    return jsonify(employees_list)

@app.route("/employees/<int:department_id>/employees", methods=['GET'])
@jwt_required()
def show_employees_by_department(department_id):

    claims = get_jwt()
    if claims['role'] not in ['admin','manager']:
        return jsonify({"error":"Only admin or manager can see all employee by department"}), 403

    error = validate_department(department_id)
    if error:
        return error

    employees_by_department = db.session.scalars(db.select(Employee).where(Employee.department_id == department_id))
    employees = [employee.to_dict() for employee in employees_by_department]
    return jsonify(employees)
    

@app.route("/employees/<int:employee_id>", methods=['GET'])
@jwt_required()
def single_employee(employee_id):

    claim = get_jwt()
    if claim['role'] not in ['admin','manager']:
        return jsonify({"error":"Only admin or manager can see employee"}), 403
    
    employee = db.get_or_404(Employee, employee_id)
    return jsonify(employee.to_dict())


@app.route("/dashboard")
@jwt_required()
def dashboard():

    claims = get_jwt()
    if claims['role'] not in ['manager','admin']:
        return jsonify({"error":"Only admin or manager can see dashborad"}), 403

    total_employees = len(db.session.scalars(db.select(Employee)).all())
    active_employees = len(db.session.scalars(db.select(Employee).where(Employee.status == "active")).all())
    inactive_employees = len(db.session.scalars(db.select(Employee).where(Employee.status == "inactive")).all())

    try:
        response = requests.get(f"{DEPARTMENT_SERVICE_URL}/departments", timeout=3)

    except requests.exceptions.RequestException:
        return jsonify({"error": "Department service is unavailable"})

    if response.status_code == 404:
        return jsonify({"error": "Department does not exist"}), 400

    department_list = response.json()
    return jsonify({
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "total_departments": len(department_list),
    })

@app.route("/employees", methods=['POST'])
@jwt_required()
def add_employee():
    claim = get_jwt()
    if not claim['role'] == "admin":
        return jsonify({"error":"Only admin can add an employee"}), 403
    
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
@jwt_required()
def update_employee(employee_id):
    claim = get_jwt()
    if not claim['role'] == "admin":
        return jsonify({"error":"Only admin can update employee status"}), 403
    
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
@jwt_required()
def delete_employee(employee_id):
    claims = get_jwt()

    if claims['role'] == "admin":
        employee = db.get_or_404(Employee, employee_id)
        db.session.delete(employee)
        db.session.commit()
        return jsonify({"message": "Employee deleted successfully"}), 200

    return jsonify({"error": "Admin access required"}), 403

if __name__ == "__main__":
    app.run(debug=True, port=5002)