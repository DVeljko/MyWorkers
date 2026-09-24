from flask import Flask, jsonify, request
from models import db, Department
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///departments.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

db.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()


@app.route("/departments", methods=["GET"])
@jwt_required()
def get_departments():

    claims = get_jwt()
    company_id = claims["company_id"]

    departments = db.session.scalars(
        db.select(Department).where(
            Department.company_id == company_id
        )
    ).all()

    return jsonify([
        department.to_dict()
        for department in departments
    ]), 200


@app.route("/departments/<int:department_id>", methods=["GET"])
@jwt_required()
def get_single_department(department_id):

    claims = get_jwt()
    company_id = claims["company_id"]

    department = db.session.scalar(
        db.select(Department).where(
            Department.id == department_id,
            Department.company_id == company_id
        )
    )

    if not department:
        return jsonify({"error": "Department not found"}), 404

    return jsonify(department.to_dict()), 200


@app.route("/departments", methods=["POST"])
@jwt_required()
def add_new_department():

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({"error": "Admin only"}), 403

    company_id = claims["company_id"]

    data = request.get_json()
    name = data["name"]

    existing_department = db.session.scalar(
        db.select(Department).where(
            Department.name == name,
            Department.company_id == company_id
        )
    )

    if existing_department:
        return jsonify({
            "error": "A department with this name already exists."
        }), 409

    new_department = Department(
        name=name,
        company_id=company_id
    )

    db.session.add(new_department)
    db.session.commit()

    return jsonify(new_department.to_dict()), 201


@app.route("/departments/<int:department_id>", methods=["PATCH"])
@jwt_required()
def update_department(department_id):

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({"error": "Admin only"}), 403

    company_id = claims["company_id"]

    department = db.session.scalar(
        db.select(Department).where(
            Department.id == department_id,
            Department.company_id == company_id
        )
    )

    if not department:
        return jsonify({"error": "Department not found"}), 404

    data = request.get_json()
    new_name = data["name"]

    existing_department = db.session.scalar(
        db.select(Department).where(
            Department.name == new_name,
            Department.company_id == company_id
        )
    )

    if existing_department and existing_department.id != department.id:
        return jsonify({
            "error": "A department with this name already exists."
        }), 409

    department.name = new_name
    db.session.commit()

    return jsonify(department.to_dict()), 200


@app.route("/departments/<int:department_id>", methods=["DELETE"])
@jwt_required()
def delete_department(department_id):

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({"error": "Admin only"}), 403

    company_id = claims["company_id"]

    department = db.session.scalar(
        db.select(Department).where(
            Department.id == department_id,
            Department.company_id == company_id
        )
    )

    if not department:
        return jsonify({"error": "Department not found"}), 404

    db.session.delete(department)
    db.session.commit()

    return jsonify({
        "message": "Department deleted successfully"
    }), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)