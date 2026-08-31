from flask import Flask, abort, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db
from dotenv import load_dotenv
import os
from functools import wraps
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

db.init_app(app)

with app.app_context():
    db.create_all()

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


        return f(*args,**kwargs)

    return check_admin

@app.route("/register", methods=['POST'])
def register():
    role = "employee"
    data = request.get_json()

    email = data.get('email')
    email_exists = db.session.scalar(db.select(User).where(User.email == email))

    if email_exists:
        return jsonify({"error": "Employee with this email already exists"}), 409

    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not password == confirm_password:
        return jsonify({'error': "Password do not match"}), 400

    new_user = User(
        email=email,
        password=generate_password_hash(password),
        role=role,
    )

    db.session.add(new_user)
    db.session.commit()
    return jsonify({"success": "Employee profile was created successfully"}) , 201

@app.route("/login", methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user_exists = db.session.scalar(db.select(User).where(User.email == email))
    if not user_exists:
        return jsonify({"error": "There is no employee with this email"}), 401

    if not check_password_hash(user_exists.password, password):
        return jsonify({"error": "Wrong password"}), 401

    login_user(user_exists)
    access_token = create_access_token(identity=str(user_exists.id), 
                                       additional_claims={
                                           "role": user_exists.role
                                       }
                                    )
    
    return jsonify({"access_token": access_token}), 200



if __name__ == "__main__":
    app.run(debug=True, port=5004)