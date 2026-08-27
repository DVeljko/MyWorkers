from flask import Flask, jsonify
from models import db, Employee

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




if __name__ == "__main__":
    app.run(debug=True)