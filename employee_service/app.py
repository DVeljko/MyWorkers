from flask import Flask, jsonify, request
from models import db, Employee
from datetime import date

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///employees.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/employees', methods=['GET'])
def get_all_employees():
    employees = db.session.scalars(db.select(Employee)).all()
    employees_list = [employee.to_dict() for employee in employees]
    return jsonify(employees_list)

@app.route("/employees/<int:employee_id>", methods=['GET'])
def single_employee(employee_id):
    employee = db.get_or_404(Employee, employee_id)
    return jsonify(employee.to_dict())

@app.route("/employees", methods=['POST'])
def add_employee():
    employee = request.get_json()
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

@app.route("/employees/<int:emloyee_id>", methods=['PATCH'])
def update_employee(employee_id):

# NAPRAVITI RUTU ZA UPDATE RADNIKA ()


if __name__ == "__main__":
    app.run(debug=True)