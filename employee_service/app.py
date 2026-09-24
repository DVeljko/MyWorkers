from flask import Flask, jsonify, request
from models import db, Employee
from datetime import date
import requests
import os
from sqlalchemy import or_
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, jwt_required, get_jwt

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


def get_auth_headers():
    return {
        "Authorization": request.headers.get("Authorization")
    }


def validate_department(department_id):
    try:
        response = requests.get(
            f"{DEPARTMENT_SERVICE_URL}/departments/{department_id}",
            headers=get_auth_headers(),
            timeout=3
        )

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Department service is unavailable"
        }), 503

    if response.status_code == 404:
        return jsonify({
            "error": "Department does not exist"
        }), 400

    if response.status_code != 200:
        return jsonify({
            "error": "Could not validate department"
        }), response.status_code

    return None


@app.route("/employees", methods=["GET"])
@jwt_required()
def get_all_employees():

    claims = get_jwt()

    if claims["role"] not in ["admin", "manager"]:
        return jsonify({
            "error": "Only admin or manager can see all employees"
        }), 403

    company_id = claims["company_id"]
    name = request.args.get("name")

    query = db.select(Employee).where(
        Employee.company_id == company_id
    )

    if name:
        query = query.where(
            or_(
                Employee.first_name.ilike(f"%{name}%"),
                Employee.last_name.ilike(f"%{name}%")
            )
        )

    employees = db.session.scalars(query).all()

    return jsonify([
        employee.to_dict()
        for employee in employees
    ]), 200


@app.route("/employees/<int:department_id>/employees", methods=["GET"])
@jwt_required()
def show_employees_by_department(department_id):

    claims = get_jwt()

    if claims["role"] not in ["admin", "manager"]:
        return jsonify({
            "error": "Only admin or manager can see employees by department"
        }), 403

    company_id = claims["company_id"]

    error = validate_department(department_id)

    if error:
        return error

    employees = db.session.scalars(
        db.select(Employee).where(
            Employee.department_id == department_id,
            Employee.company_id == company_id
        )
    ).all()

    return jsonify([
        employee.to_dict()
        for employee in employees
    ]), 200


@app.route("/employees/<int:employee_id>", methods=["GET"])
@jwt_required()
def single_employee(employee_id):

    claims = get_jwt()
    company_id = claims["company_id"]

    employee = db.session.scalar(
        db.select(Employee).where(
            Employee.id == employee_id,
            Employee.company_id == company_id
        )
    )

    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    if claims["role"] == "employee":

        if claims["employee_id"] != employee_id:
            return jsonify({
                "error": "You can only view your own profile"
            }), 403

    elif claims["role"] not in ["admin", "manager"]:
        return jsonify({
            "error": "Access denied"
        }), 403

    return jsonify(employee.to_dict()), 200


@app.route("/dashboard")
@jwt_required()
def dashboard():

    claims = get_jwt()

    if claims["role"] not in ["manager", "admin"]:
        return jsonify({
            "error": "Only admin or manager can see dashboard"
        }), 403

    company_id = claims["company_id"]

    employees = db.session.scalars(
        db.select(Employee).where(
            Employee.company_id == company_id
        )
    ).all()

    total_employees = len(employees)

    active_employees = len([
        employee for employee in employees
        if employee.status == "active"
    ])

    inactive_employees = len([
        employee for employee in employees
        if employee.status == "inactive"
    ])

    try:
        response = requests.get(
            f"{DEPARTMENT_SERVICE_URL}/departments",
            headers=get_auth_headers(),
            timeout=3
        )

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Department service is unavailable"
        }), 503

    if response.status_code != 200:
        return jsonify({
            "error": "Could not load departments"
        }), response.status_code

    department_list = response.json()

    return jsonify({
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "total_departments": len(department_list)
    }), 200


@app.route("/employees", methods=["POST"])
@jwt_required()
def add_employee():

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({
            "error": "Only admin can add an employee"
        }), 403

    company_id = claims["company_id"]

    employee = request.get_json()
    department_id = employee["department_id"]

    error = validate_department(department_id)

    if error:
        return error

    new_employee = Employee(
        first_name=employee["first_name"],
        last_name=employee["last_name"],
        email=employee["email"],
        phone=employee["phone"],
        position=employee["position"],
        hire_date=date.fromisoformat(employee["hire_date"]),
        salary=employee["salary"],
        status=employee["status"],
        department_id=department_id,
        company_id=company_id
    )

    db.session.add(new_employee)
    db.session.commit()

    return jsonify(new_employee.to_dict()), 201


@app.route("/employees/<int:employee_id>", methods=["PATCH"])
@jwt_required()
def update_employee(employee_id):

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({
            "error": "Only admin can update employee"
        }), 403

    company_id = claims["company_id"]

    employee = db.session.scalar(
        db.select(Employee).where(
            Employee.id == employee_id,
            Employee.company_id == company_id
        )
    )

    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    data = request.get_json()

    if "department_id" in data:
        error = validate_department(data["department_id"])

        if error:
            return error

    allowed_fields = [
        "phone",
        "position",
        "salary",
        "status",
        "department_id"
    ]

    for field in allowed_fields:
        if field in data:
            setattr(employee, field, data[field])

    db.session.commit()

    return jsonify(employee.to_dict()), 200


@app.route("/employee/<int:employee_id>", methods=["DELETE"])
@jwt_required()
def delete_employee(employee_id):

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    company_id = claims["company_id"]

    employee = db.session.scalar(
        db.select(Employee).where(
            Employee.id == employee_id,
            Employee.company_id == company_id
        )
    )

    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    db.session.delete(employee)
    db.session.commit()

    return jsonify({
        "message": "Employee deleted successfully"
    }), 200


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5002
    )