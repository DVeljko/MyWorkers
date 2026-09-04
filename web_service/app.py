from flask import Flask, render_template, request, session, redirect, url_for
from forms import LoginForm
import os 
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

AUTH_SERVICE = os.getenv("AUTH_SERVICE")
EMPLOYEE_SERVICE_URL = os.getenv("EMPLOYEE_SERVICE_URL")


@app.route("/login", methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        response = requests.post(
            f"{AUTH_SERVICE}/login",
            json={
                "email": email,
                "password": password
            },
            timeout=3
        )

        if response.status_code == 200:
            data = response.json()
            access_token = data['access_token']
            session['access_token'] = access_token

            return redirect(url_for("dashboard"))
        else:
            error = response.json().get("error")
            return render_template("login.html", form=form, error=error)

    return render_template("login.html", form=form)

@app.route("/dashboard")
def dashboard():
    token = session.get('access_token')

    if not token:
        return redirect(url_for('login'))

    response = requests.get(
        f"{EMPLOYEE_SERVICE_URL}/dashboard",
        headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=3
    )

    if response.status_code != 200:
        return redirect(url_for('login'))

    data = response.json()

    return render_template(
        "dashboard.html",
        total_employees=data["total_employees"],
        active_employees=data["active_employees"],
        inactive_employees=data["inactive_employees"],
        total_departments=data["total_departments"]
    )



if __name__ == "__main__":
    app.run(debug=True)