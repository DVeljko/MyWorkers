from flask import Flask, jsonify, request

from models import db, Department

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///departments.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/departments", methods=['GET'])
def get_departments():
    departments = db.session.scalars(db.select(Department)).all()
    departments_list = [department.to_dict() for department in departments]
    return jsonify(departments_list)

@app.route("/departments/<int:department_id>", methohds=['GET'])
def get_single_department(department_id):
    department = db.get_or_404(Department, department_id)
    return jsonify(department.to_dict())

@app.route("/new-department", methods=['POST'])
def add_new_department():
    data = request.get_json()
    name = data['name']

    existing_department = db.session.scalar(
        db.select(Department).where(Department.name == name)
    )

    if existing_department:
        return jsonify({"error": "A department with this name already exists."}), 409

    new_department = Department(name=name)
    db.session.add(new_department)
    db.session.commit()

    return jsonify(new_department.to_dict()), 201


if __name__ == "__main__":
    app.run(debug=True)