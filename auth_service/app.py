from flask import Flask, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db
from dotenv import load_dotenv
import os
from functools import wraps


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager(app)

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







if __name__ == "__main__":
    app.run(debug=True, port=5004)