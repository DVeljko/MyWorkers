from flask import Flask, render_template, request, session, redirect, url_for
from forms import LoginForm, AddEmployee, AddDepartment
import os 
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

AUTH_SERVICE = os.getenv("AUTH_SERVICE")
EMPLOYEE_SERVICE_URL = os.getenv("EMPLOYEE_SERVICE_URL")
DEPARTMENT_SERVICE_URL = os.getenv("DEPARTMENT_SERVICE_URL")
ATTENDANCE_SERVICE_URL = os.getenv("ATTENDANCE_SERVICE_URL")

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

    search = request.args.get("search")
    if search:
        response = requests.get(
            f"{EMPLOYEE_SERVICE_URL}/employees",

            params={
                "name": search
            },

            headers={
                "Authorization": f"Bearer {token}"
            },

            timeout=3
        )

        if response.status_code != 200:
            error = response.json().get("error", "Something went wrong.")
            return render_template(
                "employees.html",
                employees=[],
                error=error
            )

        employee_list = response.json()
        return render_template("employees.html", employees=employee_list)

    
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
        error = response.json().get('error', "Something went wrong.")
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


@app.route("/employees/<int:employee_id>")
def employee_profile(employee_id):

    token = session.get("access_token")

    if not token:
        return redirect(url_for("login"))

    response = requests.get(
        f"{EMPLOYEE_SERVICE_URL}/employees/{employee_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=3
    )

    if response.status_code == 200:
        employee = response.json()

        return render_template(
            "employee_profile.html",
            employee=employee
        )

    error = response.json().get("error", "Something went wrong.")

    return render_template(
        "employee_profile.html",
        employee=None,
        error=error
    )


@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
def edit_employee(employee_id):

    token = session.get("access_token")

    if not token:
        return redirect(url_for("login"))

    form = AddEmployee()

    response = requests.get(
        f"{EMPLOYEE_SERVICE_URL}/employees/{employee_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=3
    )

    if response.status_code != 200:
        error = response.json().get(
            "error",
            "Something went wrong."
        )

        return render_template(
            "edit_employee.html",
            form=form,
            employee=None,
            error=error
        )

    employee = response.json()

    if form.validate_on_submit():

        patch_response = requests.patch(
            f"{EMPLOYEE_SERVICE_URL}/employees/{employee_id}",
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

        if patch_response.status_code == 200:
            return redirect(
                url_for(
                    "employee_profile",
                    employee_id=employee_id
                )
            )

        error = patch_response.json().get(
            "error",
            "Something went wrong."
        )

        return render_template(
            "edit_employee.html",
            form=form,
            employee=employee,
            error=error
        )

    if request.method == "GET":
        form.first_name.data = employee["first_name"]
        form.last_name.data = employee["last_name"]
        form.email.data = employee["email"]
        form.phone.data = employee["phone"]
        form.position.data = employee["position"]

        form.hire_date.data = datetime.strptime(
            employee["hire_date"],
            "%Y-%m-%d"
        ).date()

        form.salary.data = employee["salary"]
        form.status.data = employee["status"]
        form.department_id.data = employee["department_id"]

    return render_template(
        "edit_employee.html",
        form=form,
        employee=employee
    )




@app.route("/employee/<int:employee_id>/delete", methods=['POST'])
def delete_employee(employee_id):
    token = session.get('access_token')

    if not token:
        return redirect(url_for("login"))

    response= requests.delete(
        f"{EMPLOYEE_SERVICE_URL}/employee/{employee_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=3
    )

    if response.status_code == 200:
        return redirect(url_for("all_employees"))
    
    else:
        error = response.json().get("error", "Something went wrong.")

        return render_template(
            "employee_profile.html",
            employee=None,
            error=error
        )

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
    print(data)

    return render_template(
        "dashboard.html",
        total_employees=data["total_employees"],
        active_employees=data["active_employees"],
        inactive_employees=data["inactive_employees"],
        total_departments=data["total_departments"]
    )

@app.route("/departments")
def departments():
    token = session.get("access_token")

    if not token:
        return redirect(url_for("login"))

    response = requests.get(
        f"{DEPARTMENT_SERVICE_URL}/departments",
        timeout=3
    )

    if response.status_code != 200:
        return redirect(url_for('login'))

    departments = response.json()
    return render_template("departments.html", departments=departments)

@app.route("/department/add", methods=['GET','POST'])
def add_department():
    token = session.get('access_token')

    if not token:
        return redirect(url_for("login"))

    form = AddDepartment()
    if form.validate_on_submit():
        name = form.name.data
        response = requests.post(
            f"{DEPARTMENT_SERVICE_URL}/departments",
            json={
                "name": name
            },
            timeout=3
        )

        if response.status_code == 201:
            return redirect(url_for("departments"))

        else:
            error = response.json().get('error')
            return render_template(
                "add_department.html",
                form=form,
                error=error
            )


    return render_template("add_department.html", form=form)

@app.route("/department/<int:department_id>/edit", methods=['GET', 'POST'])
def edit_department(department_id):

    token = session.get('access_token')
    if not token:
        return redirect(url_for("login"))

    form = AddDepartment()
    response = requests.get(
        f"{DEPARTMENT_SERVICE_URL}/departments/{department_id}",
        timeout=3
    )

    if response.status_code != 200:
        error = response.json().get(
            "error",
            "Something went wrong."
        )

        return render_template(
            "edit_department.html",
            form=form,
            error=error
        )

    department = response.json()

    if form.validate_on_submit():
        edit_response = requests.patch(
            f"{DEPARTMENT_SERVICE_URL}/departments/{department_id}",
            json={
                'name': form.name.data
            },
            timeout=3

        )

        if edit_response.status_code == 200:
            return redirect(url_for("departments"))

        error = edit_response.json().get('error')
        return render_template('edit_department.html', form=form,error=error)


    if request.method == "GET":
        form.name.data = department['name']

    return render_template('edit_department.html', form=form, department=department)

@app.route("/department/delete/<int:department_id>", methods=['POST'])
def delete_department(department_id):

    token = session.get('access_token')
    if not token:
        return redirect(url_for("login"))

    response = requests.delete(
        f"{DEPARTMENT_SERVICE_URL}/departments/{department_id}",
        timeout=3
    )

    if response.status_code != 200:
        error = response.json().get('error')
        return render_template('departments.html', error=error, departments=[])

    return redirect(url_for("departments"))

@app.route("/attendance")
def attendance():
    token = session.get('access_token')

    if not token:
        return redirect(url_for("login"))

    response = requests.get(
        f"{ATTENDANCE_SERVICE_URL}/attendance",
        headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=3
    )

    if response.status_code == 200:
        data = response.json()
        return render_template("attendance.html", attendances=data)
    else:
        error = response.json().get('error')
        return render_template("attendance.html", attendances=[], error=error)

@app.route("/attendance/check-in/<int:employee_id>", methods=["POST"])
def check_in(employee_id):

    token = session.get("access_token")

    if not token:
        return redirect(url_for("login"))

    response = requests.post(
        f"{ATTENDANCE_SERVICE_URL}/attendance/{employee_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=3
    )

    if response.status_code == 201:
        return redirect(url_for("attendance"))

    error = response.json().get("error")

    attendance_response = requests.get(
        f"{ATTENDANCE_SERVICE_URL}/attendance",
        headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=3
    )

    attendances = attendance_response.json()

    return render_template(
        "attendance.html",
        attendances=attendances,
        error=error
    )

@app.route("/attendance/check-out/<int:employee_id>", methods=['POST'])
def check_out(employee_id):
    token = session.get("access_token")
    if not token:
        return redirect(url_for("login"))

    response = requests.patch(
        f"{ATTENDANCE_SERVICE_URL}/attendance/{employee_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=3
    )

    if response.status_code == 200:
        return redirect(url_for("attendance"))

    error = response.json().get('error')

    attendance_response = requests.get(
        f"{ATTENDANCE_SERVICE_URL}/attendance",
                headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=3

    )

    attendances = attendance_response.json()

    return render_template(
        "attendance.html",
        attendances=attendances,
        error=error
    )

@app.route("/logout", methods=["GET","POST"])
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)