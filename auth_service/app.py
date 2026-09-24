from flask import Flask, abort, request, jsonify
from flask_login import LoginManager, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db, Company, RegistrationRequest
from dotenv import load_dotenv
import os
from functools import wraps
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt
)
from flask_migrate import Migrate
import requests


load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

EMPLOYEE_SERVICE_URL = os.getenv("EMPLOYEE_SERVICE_URL")

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
jwt = JWTManager(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(f):
    @wraps(f)
    def check_admin(*args, **kwargs):

        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)

        return f(*args, **kwargs)

    return check_admin


# --------------------------------------------------
# CREATE COMPANY + ADMIN
# --------------------------------------------------

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    company_name = data.get("company_name")
    owner_first_name = data.get("owner_first_name")
    owner_last_name = data.get("owner_last_name")

    email_exists = db.session.scalar(
        db.select(User).where(User.email == email)
    )

    if email_exists:
        return jsonify({
            "error": "Employee with this email already exists"
        }), 409

    company_exists = db.session.scalar(
        db.select(Company).where(
            Company.name == company_name
        )
    )

    if company_exists:
        return jsonify({
            "error": "This company already exists!"
        }), 409

    if password != confirm_password:
        return jsonify({
            "error": "Password do not match"
        }), 400

    new_company = Company(
        name=company_name,
        owner_first_name=owner_first_name,
        owner_last_name=owner_last_name
    )

    db.session.add(new_company)

    # Dobijemo company ID prije commit-a
    db.session.flush()

    new_user = User(
        email=email,
        company_id=new_company.id,
        password=generate_password_hash(password),
        role="admin"
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "success": "Company and admin account created successfully"
    }), 201


# --------------------------------------------------
# EMPLOYEE REGISTRATION REQUEST
# --------------------------------------------------

@app.route("/register-employee", methods=["POST"])
def register_employee():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    company_id = data.get("company_id")

    email_exists = db.session.scalar(
        db.select(User).where(
            User.email == email
        )
    )

    if email_exists:
        return jsonify({
            "error": "Employee with this email already exists"
        }), 409

    if password != confirm_password:
        return jsonify({
            "error": "Password do not match"
        }), 400

    registration_request_exists = db.session.scalar(
        db.select(RegistrationRequest).where(
            RegistrationRequest.email == email
        )
    )

    if registration_request_exists:
        return jsonify({
            "error": "Registration request already exists"
        }), 409

    company_exists = db.session.scalar(
        db.select(Company).where(
            Company.id == company_id
        )
    )

    if not company_exists:
        return jsonify({
            "error": "There is no company with that ID"
        }), 404

    new_request = RegistrationRequest(
        company_id=company_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=generate_password_hash(password)
    )

    db.session.add(new_request)
    db.session.commit()

    return jsonify({
        "success": "Registration request sent successfully"
    }), 201


# --------------------------------------------------
# GET PENDING REGISTRATION REQUESTS
# --------------------------------------------------

@app.route("/registration-requests", methods=["GET"])
@jwt_required()
def get_registration_requests():

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    company_id = claims["company_id"]

    registration_requests = db.session.scalars(
        db.select(RegistrationRequest).where(
            RegistrationRequest.company_id == company_id,
            RegistrationRequest.status == "pending"
        )
    ).all()

    data = []

    for registration_request in registration_requests:
        data.append({
            "id": registration_request.id,
            "first_name": registration_request.first_name,
            "last_name": registration_request.last_name,
            "email": registration_request.email,
            "status": registration_request.status
        })

    return jsonify(data), 200


# --------------------------------------------------
# ACCEPT REGISTRATION REQUEST
# --------------------------------------------------

@app.route(
    "/registration-requests/<int:request_id>/accept",
    methods=["POST"]
)
@jwt_required()
def accept_registration_request(request_id):

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({
            "error": "Admin only"
        }), 403

    company_id = claims["company_id"]

    registration_request = db.session.scalar(
        db.select(RegistrationRequest).where(
            RegistrationRequest.id == request_id
        )
    )

    if not registration_request:
        return jsonify({
            "error": "Registration request not found"
        }), 404

    if registration_request.company_id != company_id:
        return jsonify({
            "error": "This request does not belong to your company"
        }), 403

    if registration_request.status != "pending":
        return jsonify({
            "error": "Registration request is not pending"
        }), 400

    data = request.get_json()

    token = request.headers.get("Authorization")

    try:
        response = requests.post(
            f"{EMPLOYEE_SERVICE_URL}/employees",
            headers={
                "Authorization": token
            },
            json={
                "first_name": registration_request.first_name,
                "last_name": registration_request.last_name,
                "email": registration_request.email,
                "phone": data["phone"],
                "position": data["position"],
                "hire_date": data["hire_date"],
                "salary": data["salary"],
                "status": "active",
                "department_id": data["department_id"]
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Employee service is unavailable"
        }), 503

    if response.status_code != 201:
        return jsonify({
            "error": "Could not create employee"
        }), response.status_code

    employee = response.json()

    new_user = User(
        email=registration_request.email,
        password=registration_request.password,
        role="employee",
        employee_id=employee["id"],
        company_id=company_id
    )

    db.session.add(new_user)

    registration_request.status = "accepted"

    db.session.commit()

    return jsonify({
        "success": "Registration request accepted",
        "employee_id": employee["id"]
    }), 200


# --------------------------------------------------
# REJECT REGISTRATION REQUEST
# --------------------------------------------------

@app.route(
    "/registration-requests/<int:request_id>/reject",
    methods=["POST"]
)
@jwt_required()
def reject_registration_request(request_id):

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({
            "error": "Admin only"
        }), 403

    company_id = claims["company_id"]

    registration_request = db.session.scalar(
        db.select(RegistrationRequest).where(
            RegistrationRequest.id == request_id
        )
    )

    if not registration_request:
        return jsonify({
            "error": "Registration request not found"
        }), 404

    if registration_request.company_id != company_id:
        return jsonify({
            "error": "This request does not belong to your company"
        }), 403

    if registration_request.status != "pending":
        return jsonify({
            "error": "Registration request is not pending"
        }), 400

    registration_request.status = "rejected"

    db.session.commit()

    return jsonify({
        "success": "Registration request rejected"
    }), 200


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user_exists = db.session.scalar(
        db.select(User).where(
            User.email == email
        )
    )

    if not user_exists:
        return jsonify({
            "error": "There is no employee with this email"
        }), 401

    if not check_password_hash(
        user_exists.password,
        password
    ):
        return jsonify({
            "error": "Wrong password"
        }), 401

    login_user(user_exists)

    access_token = create_access_token(
        identity=str(user_exists.id),
        additional_claims={
            "role": user_exists.role,
            "employee_id": user_exists.employee_id,
            "company_id": user_exists.company_id
        }
    )

    return jsonify({
        "access_token": access_token,
        "role": user_exists.role,
        "employee_id": user_exists.employee_id
    }), 200


# --------------------------------------------------
# EDIT USER ROLE
# --------------------------------------------------

@app.route("/users/<int:user_id>/role", methods=["PATCH"])
@jwt_required()
def edit_user_role(user_id):

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    company_id = claims["company_id"]

    user = db.session.scalar(
        db.select(User).where(
            User.id == user_id,
            User.company_id == company_id
        )
    )

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    data = request.get_json()

    role = data.get("role")

    if role not in ["manager", "employee", "admin"]:
        return jsonify({
            "error": "Role is not valid"
        }), 400

    user.role = role

    db.session.commit()

    return jsonify({
        "success": "User role updated successfully",
        "user_id": user.id,
        "role": user.role
    }), 200


# --------------------------------------------------
# LINK USER TO EMPLOYEE
# --------------------------------------------------

@app.route("/users/<int:user_id>/employee", methods=["PATCH"])
@jwt_required()
def link_user_employee(user_id):

    claims = get_jwt()

    if claims["role"] != "admin":
        return jsonify({
            "error": "Admin access required"
        }), 403

    company_id = claims["company_id"]

    user = db.session.scalar(
        db.select(User).where(
            User.id == user_id,
            User.company_id == company_id
        )
    )

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    data = request.get_json()

    employee_id = data.get("employee_id")

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
        return jsonify({
            "error": "Employee service is unavailable"
        }), 503

    if response.status_code == 404:
        return jsonify({
            "error": "Employee does not exist"
        }), 400

    if response.status_code != 200:
        return jsonify({
            "error": "Could not validate employee"
        }), response.status_code

    employee = response.json()

    if user.email != employee["email"]:
        return jsonify({
            "error": "User email and employee email do not match"
        }), 400

    user.employee_id = employee_id

    db.session.commit()

    return jsonify({
        "success": "User linked to employee successfully",
        "user_id": user.id,
        "employee_id": user.employee_id
    }), 200


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5004
    )