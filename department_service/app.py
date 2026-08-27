from flask import Flask, jsonify

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



if __name__ == "__main__":
    app.run(debug=True)