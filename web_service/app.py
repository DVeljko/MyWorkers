from flask import Flask, render_template, request, session, redirect, url_for
from forms import LoginForm, AddEmployee
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

@app.route("/employees")
def all_employees():
    token = session.get('access_token')
    if not token:
        return redirect(url_for('login'))

    
    response = requests.get(
        f"{EMPLOYEE_SERVICE_URL}/employees",
        headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=3

    )

    if response.status_code == 200:
        employees = response.json()
        return render_template(
            "employees.html",
            employees=employees
        )

    else:
        error = response.json().get('error')
        return render_template("employees.html", employees=[], error=error)

@app.route("/employees/add", methods=["GET", "POST"])
def add_employee():

    token = session.get("access_token")
    if not token:
        return redirect(url_for("login"))
    
    form = AddEmployee()
    if form.validate_on_submit():
        response = requests.post(
            f"{EMPLOYEE_SERVICE_URL}/employees",
            headers={
                "Authorization": f"Bearer {token}"
            },
            json={
                "first_name": form.first_name.data,
                "last_name": form.last_name.data,
                "email": form.email.data,
                "phone": form.phone.data,
                "position": form.position.data,
                "hire_date": form.hire_date.data.isoformat(),
                "salary": form.salary.data,
                "status": form.status.data,
                "department_id": form.department_id.data,
            },
            timeout=3
        )

        if response.status_code == 201:
            return redirect(url_for("all_employees"))

        else:
            error = response.json().get("error", "Something went wrong.")
            return render_template(
                "add_employee.html",
                form=form,
                error=error
            )



    return render_template("add_employee.html", form=form)

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