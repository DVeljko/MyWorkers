from flask import Flask, render_template, request, session, redirect, url_for
from forms import LoginForm, AddEmployee, AddDepartment, RegisterForm, EmployeeRegisterForm, AcceptEmployeeForm
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
from functools import wraps


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

AUTH_SERVICE = os.getenv("AUTH_SERVICE")
EMPLOYEE_SERVICE_URL = os.getenv("EMPLOYEE_SERVICE_URL")
DEPARTMENT_SERVICE_URL = os.getenv("DEPARTMENT_SERVICE_URL")
ATTENDANCE_SERVICE_URL = os.getenv("ATTENDANCE_SERVICE_URL")


def handle_unauthorized(response):
    if response.status_code == 401:
        session.clear()
        return True
    return False


def service_request_failed():
    return render_template(
        "service_error.html",
        error="Service is currently unavailable."
    ), 503


def get_json_response(response, default=None):
    
    try:
        return response.json()
    
    except (requests.exceptions.JSONDecodeError, ValueError):
        return {} if default is None else default


def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def check_role(*args, **kwargs):

            if not session.get("access_token"):
                return redirect(url_for("index"))
            
            if session.get("role") not in allowed_roles:

                if session.get("role") == "employee":

                    return redirect(
                        url_for(
                            "employee_profile",
                            employee_id=session.get("employee_id")
                        )

                    )
                
                return redirect(url_for("dashboard"))
            
            return f(*args, **kwargs)
        
        return check_role
    
    return decorator


@app.route("/")
def index():

    token = session.get("access_token")
    employee_role = session.get("role")
    employee_id = session.get("employee_id")

    if not token:
        return render_template("auth.html",
            login_form=LoginForm(),
            employee_form=EmployeeRegisterForm(),
            register_form=RegisterForm()
        )
    
    if employee_role == "employee":
        return redirect(
            url_for("employee_profile", employee_id=employee_id)
        )
    
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        try:
            response = requests.post(
                f"{AUTH_SERVICE}/login",
                json={
                    "email": email,
                    "password": password
                },
                timeout=3
            )

        except requests.exceptions.RequestException:
            return service_request_failed()
        
        if response.status_code == 200:

            data = get_json_response(response)
            access_token = data["access_token"]
            role = data["role"]
            employee_id = data["employee_id"]
            session["access_token"] = access_token
            session["role"] = role
            session["employee_id"] = employee_id
            # Employee ide direktno na svoj profil

            if role == "employee":
                return redirect(
                    url_for(
                        "employee_profile",
                        employee_id=employee_id
                    )
                )
            # Admin i manager idu na dashboard
            return redirect(url_for("dashboard"))
        
        else:
            error = get_json_response(response).get("error")

            return render_template(
                "auth.html",
                login_form=form,
                employee_form=EmployeeRegisterForm(),
                register_form=RegisterForm(),
                login_error=error
            )
        
    return render_template(
        "auth.html",
        login_form=form,
        employee_form=EmployeeRegisterForm(),
        register_form=RegisterForm(),
        active_tab="login"
    )


@app.route("/create-company", methods=['GET', 'POST'])
def create_company():

    form = RegisterForm()

    if form.validate_on_submit():
        owner_first_name = form.owner_first_name.data
        owner_last_name = form.owner_last_name.data
        company_name = form.company_name.data
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        try:
            response = requests.post(
                f"{AUTH_SERVICE}/register",
                json={
                    "owner_first_name": owner_first_name,
                    "owner_last_name": owner_last_name,
                    "company_name": company_name,
                    "email": email,
                    "password": password,
                    "confirm_password": confirm_password,
                },
                timeout=3,
            )
        except requests.exceptions.RequestException:
            return service_request_failed()
        
        if response.status_code != 201:
            error = get_json_response(response).get("error", "Something went wrong.")
            return render_template(
                "auth.html",
                login_form=LoginForm(),
                employee_form=EmployeeRegisterForm(),
                register_form=form,
                register_error=error,
                active_tab="company"
            )
        try:
            login_response = requests.post(
                f"{AUTH_SERVICE}/login",
                json={
                    "email": email,
                    "password": password
                },
                timeout=3
            )

        except requests.exceptions.RequestException:
            return service_request_failed()
        
        if login_response.status_code != 200:

            error = get_json_response(login_response).get("error", "Login failed.")

            return render_template(
                "auth.html",
                login_form=LoginForm(),
                employee_form=EmployeeRegisterForm(),
                register_form=form,
                register_error=error,
                active_tab="company"
            )
        data = get_json_response(login_response)
        session["access_token"] = data["access_token"]
        session["role"] = data["role"]
        session["employee_id"] = data["employee_id"]

        return redirect(url_for("dashboard"))
    
    return render_template(
        "auth.html",
        login_form=LoginForm(),
        employee_form=EmployeeRegisterForm(),
        register_form=form,
        active_tab="company"
    )


@app.route("/register-employee", methods=["POST"])
def register_employee():
    form = EmployeeRegisterForm()

    if form.validate_on_submit():

        first_name = form.first_name.data
        last_name = form.last_name.data
        company_id = form.company_id.data
        email = form.email.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        try:
            response = requests.post(
                f"{AUTH_SERVICE}/register-employee",
                json={
                    "company_id": company_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "password": password,
                    "confirm_password": confirm_password,
                },
                timeout=3
            )
        except requests.exceptions.RequestException:
            return service_request_failed()
        
        # Ako registracija nije uspjela
        if response.status_code != 201:
            error = get_json_response(response).get(
                "error",
                "Could not send registration request."
            )
            return render_template(
                "auth.html",
                login_form=LoginForm(),
                employee_form=form,
                register_form=RegisterForm(),
                employee_error=error,
                active_tab="employee"
            )
        
        # Ako je zahtjev uspješno poslan
        return render_template(
            "registration_request_success.html"
        )
    
    # Ako WTForms validacija nije prošla
    return render_template(
        "auth.html",
        login_form=LoginForm(),
        employee_form=form,
        register_form=RegisterForm(),
        active_tab="employee"
    )


@app.route("/employees")
@roles_required("admin", "manager")
def all_employees():

    token = session.get('access_token')

    if not token:
        return redirect(url_for('index'))
    
    search = request.args.get("search")

    if search:
        try:
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

        except requests.exceptions.RequestException:
            return service_request_failed()
        
        if handle_unauthorized(response):
            return redirect(url_for("index"))
        
        if response.status_code != 200:
            error = get_json_response(response).get("error", "Something went wrong.")
            return render_template(
                "employees.html",
                employees=[],
                error=error
            )
        
        employee_list = get_json_response(response)
        return render_template("employees.html", employees=employee_list)
    try:

        response = requests.get(
            f"{EMPLOYEE_SERVICE_URL}/employees",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code == 200:

        employees = get_json_response(response)
        return render_template(
            "employees.html",
            employees=employees
        )
    
    else:
        error = get_json_response(response).get('error', "Something went wrong.")
        return render_template("employees.html", employees=[], error=error)


@app.route("/employees/add", methods=["GET", "POST"])
@roles_required("admin")
def add_employee():

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    form = AddEmployee()

    # Get departments from department_service
    try:
        department_response = requests.get(
            f"{DEPARTMENT_SERVICE_URL}/departments",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if department_response.status_code == 200:

        departments = get_json_response(department_response)
        form.department_id.choices = [(department["id"], department["name"])for department in departments]

    if form.validate_on_submit():

        try:
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

        except requests.exceptions.RequestException:
            return service_request_failed()
        
        if handle_unauthorized(response):
            return redirect(url_for("index"))
        
        if response.status_code == 201:
            return redirect(url_for("all_employees"))
        
        error = get_json_response(response).get(
            "error",
            "Something went wrong."
        )

        return render_template(
            "add_employee.html",
            form=form,
            error=error
        )
    
    return render_template(
        "add_employee.html",
        form=form
    )


@app.route("/employees/<int:employee_id>")
def employee_profile(employee_id):

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    try:
        response = requests.get(
            f"{EMPLOYEE_SERVICE_URL}/employees/{employee_id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code == 200:
        employee = get_json_response(response)
        department_id = employee['department_id']
        try:

            department_response = requests.get(
                f"{DEPARTMENT_SERVICE_URL}/departments/{department_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=3
            )

        except requests.exceptions.RequestException:
            return service_request_failed()
        
        if department_response.status_code != 200:
            return render_template(
                "employee_profile.html",
                employee=employee,
                error="Could not load department"
            )
        
        department = get_json_response(department_response)
        department_name = department['name']

        return render_template(
            "employee_profile.html",
            employee=employee,
            department_name = department_name
        )
    
    error = get_json_response(response).get("error", "Something went wrong.")

    return render_template(
        "employee_profile.html",
        employee=None,
        error=error
    )


@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@roles_required("admin")
def edit_employee(employee_id):

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    form = AddEmployee()
    try:

        department_response = requests.get(
            f"{DEPARTMENT_SERVICE_URL}/departments",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if department_response.status_code == 200:
        departments = get_json_response(department_response)

        form.department_id.choices = [(department["id"], department["name"])for department in departments
        ]
    try:

        response = requests.get(
            f"{EMPLOYEE_SERVICE_URL}/employees/{employee_id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code != 200:
        error = get_json_response(response).get(
            "error",
            "Something went wrong."
        )

        return render_template(
            "edit_employee.html",
            form=form,
            employee=None,
            error=error
        )
    
    employee = get_json_response(response)

    if form.validate_on_submit():

        try:
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

        except requests.exceptions.RequestException:
            return service_request_failed()
        
        if handle_unauthorized(patch_response):
            return redirect(url_for("index"))
        
        if patch_response.status_code == 200:
            return redirect(
                url_for(
                    "employee_profile",
                    employee_id=employee_id
                )
            )
        
        error = get_json_response(patch_response).get(
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
        form.hire_date.data = datetime.strptime(employee["hire_date"],"%Y-%m-%d").date()

        form.salary.data = employee["salary"]
        form.status.data = employee["status"]
        form.department_id.data = employee["department_id"]

    return render_template(
        "edit_employee.html",
        form=form,
        employee=employee
    )


@app.route("/employee/<int:employee_id>/delete", methods=['POST'])
@roles_required("admin")
def delete_employee(employee_id):

    token = session.get('access_token')

    if not token:
        return redirect(url_for("index"))
    
    try:
        response= requests.delete(
            f"{EMPLOYEE_SERVICE_URL}/employee/{employee_id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code == 200:
        return redirect(url_for("all_employees"))
    
    else:
        error = get_json_response(response).get("error", "Something went wrong.")
        return render_template(
            "employee_profile.html",
            employee=None,
            error=error
        )


@app.route("/dashboard")
@roles_required("admin", "manager")
def dashboard():

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    try:
        response = requests.get(
            f"{EMPLOYEE_SERVICE_URL}/dashboard",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code != 200:
        error = get_json_response(response).get(
            "error",
            "Could not load dashboard."
        )

        return render_template(
            "dashboard.html",
            total_employees=0,
            active_employees=0,
            inactive_employees=0,
            total_departments=0,
            error=error
        )
    
    data = get_json_response(response)

    return render_template(
        "dashboard.html",
        total_employees=data["total_employees"],
        active_employees=data["active_employees"],
        inactive_employees=data["inactive_employees"],
        total_departments=data["total_departments"]
    )


@app.route("/departments")
@roles_required("admin", "manager")
def departments():

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    try:
        response = requests.get(
            f"{DEPARTMENT_SERVICE_URL}/departments",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code != 200:
        print(
            "DEPARTMENT ERROR:",
            response.status_code,
            response.text
        )

        return render_template(
            "departments.html",
            departments=[],
            error=response.text
        )
    
    departments = get_json_response(response)

    return render_template(
        "departments.html",
        departments=departments
    )


@app.route("/department/add", methods=["GET", "POST"])
@roles_required("admin")
def add_department():

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    form = AddDepartment()

    if form.validate_on_submit():
        name = form.name.data

        try:
            response = requests.post(
                f"{DEPARTMENT_SERVICE_URL}/departments",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "name": name
                },
                timeout=3
            )
        except requests.exceptions.RequestException:
            return service_request_failed()
        
        if handle_unauthorized(response):
            return redirect(url_for("index"))
        
        if response.status_code == 201:
            return redirect(url_for("departments"))
        
        try:
            error = get_json_response(response).get(
                "error",
                "Could not add department."
            )

        except requests.exceptions.JSONDecodeError:
            error = (
                f"Department service error "
                f"({response.status_code}). Check terminal logs."
            )

        return render_template(
            "add_department.html",
            form=form,
            error=error
        )
    
    return render_template(
        "add_department.html",
        form=form
    )


@app.route("/department/<int:department_id>/edit", methods=['GET', 'POST'])
@roles_required("admin")
def edit_department(department_id):

    token = session.get('access_token')

    if not token:
        return redirect(url_for("index"))
    
    form = AddDepartment()

    try:
        response = requests.get(
            f"{DEPARTMENT_SERVICE_URL}/departments/{department_id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )
    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if response.status_code != 200:
        error = get_json_response(response).get(
            "error",
            "Something went wrong."
        )

        return render_template(
            "edit_department.html",
            form=form,
            error=error
        )
    
    department = get_json_response(response)

    if form.validate_on_submit():
        try:
            edit_response = requests.patch(
                f"{DEPARTMENT_SERVICE_URL}/departments/{department_id}",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    'name': form.name.data
                },
                timeout=3
            )

        except requests.exceptions.RequestException:
            return service_request_failed()
        
        if edit_response.status_code == 200:
            return redirect(url_for("departments"))
        
        error = get_json_response(edit_response).get('error')

        return render_template('edit_department.html', form=form,error=error)
    
    if request.method == "GET":
        form.name.data = department['name']

    return render_template('edit_department.html', form=form, department=department)


@app.route("/department/delete/<int:department_id>", methods=['POST'])
@roles_required("admin")
def delete_department(department_id):
    token = session.get('access_token')

    if not token:
        return redirect(url_for("index"))
    
    try:
        response = requests.delete(
            f"{DEPARTMENT_SERVICE_URL}/departments/{department_id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if response.status_code != 200:

        error = get_json_response(response).get('error')
        return render_template('departments.html', error=error, departments=[])
    
    return redirect(url_for("departments"))


@app.route("/attendance")
@roles_required("admin", "manager")
def attendance():

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    try:
        response = requests.get(
            f"{ATTENDANCE_SERVICE_URL}/attendance",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code == 200:
        data = get_json_response(response)

        for attendance in data:
            attendance["arrival_time"] = datetime.fromisoformat(attendance["arrival_time"]).strftime("%d.%m.%Y. %H:%M")

            if attendance["departure_time"]:
                attendance["departure_time"] = datetime.fromisoformat(attendance["departure_time"]).strftime("%d.%m.%Y. %H:%M")

        return render_template(
            "attendance.html",
            attendances=data
        )
    error = get_json_response(response).get(
        "error",
        "Something went wrong."
    )
    return render_template(
        "attendance.html",
        attendances=[],
        error=error
    )


@app.route("/attendance/check-in/<int:employee_id>", methods=["POST"])
def check_in(employee_id):

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    try:
        response = requests.post(
            f"{ATTENDANCE_SERVICE_URL}/attendance/{employee_id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()

    
    if handle_unauthorized(response):
        return redirect(url_for("index"))

    
    if response.status_code == 201:

        if session.get("role") == "employee":
            return redirect(url_for("my_attendance"))
        
        return redirect(url_for("attendance"))
    
    error = get_json_response(response).get("error")

    if session.get("role") == "employee":
        return render_template(
            "my_attendance.html",
            attendances=[],
            error=error
        )
    try:

        attendance_response = requests.get(
            f"{ATTENDANCE_SERVICE_URL}/attendance",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(attendance_response):
        return redirect(url_for("index"))
    
    attendances = get_json_response(attendance_response)

    return render_template(
        "attendance.html",
        attendances=attendances,
        error=error
    )


@app.route("/attendance/check-out/<int:employee_id>", methods=["POST"])
def check_out(employee_id):

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    try:
        response = requests.patch(
            f"{ATTENDANCE_SERVICE_URL}/attendance/{employee_id}",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code == 200:

        if session.get("role") == "employee":
            return redirect(url_for("my_attendance"))
        
        return redirect(url_for("attendance"))
    
    error = get_json_response(response).get("error")

    if session.get("role") == "employee":

        return render_template(
            "my_attendance.html",
            attendances=[],
            error=error
        )
    try:
        attendance_response = requests.get(
            f"{ATTENDANCE_SERVICE_URL}/attendance",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(attendance_response):
        return redirect(url_for("index"))
    
    attendances = get_json_response(attendance_response)

    return render_template(
        "attendance.html",
        attendances=attendances,
        error=error
    )


@app.route("/registration-requests")
@roles_required("admin")
def registration_requests():

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    try:
        response = requests.get(
            f"{AUTH_SERVICE}/registration-requests",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code != 200:
        error = get_json_response(response).get(
            "error",
            "Could not load registration requests."
        )

        return render_template(
            "registration_requests.html",
            registration_requests=[],
            error=error
        )
    
    registration_requests = get_json_response(response)

    return render_template(
        "registration_requests.html",
        registration_requests=registration_requests
    )


@app.route("/registration-requests/<int:request_id>/accept",methods=["GET", "POST"])
@roles_required("admin")
def accept_registration_request(request_id): 

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    form = AcceptEmployeeForm()
    # Učitaj departments samo iz adminove kompanije

    try:
        department_response = requests.get(
            f"{DEPARTMENT_SERVICE_URL}/departments",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(department_response):
        return redirect(url_for("index"))
    
    if department_response.status_code != 200:
        return render_template(
            "accept_registration_request.html",
            form=form,
            error="Could not load departments."
        )
    
    departments = get_json_response(department_response)

    form.department_id.choices = [(department["id"], department["name"])for department in departments]

    if form.validate_on_submit():

        try:
            response = requests.post(
                f"{AUTH_SERVICE}/registration-requests/{request_id}/accept",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                json={
                    "phone": form.phone.data,
                    "position": form.position.data,
                    "hire_date": form.hire_date.data.isoformat(),
                    "salary": form.salary.data,
                    "department_id": form.department_id.data
                },
                timeout=3
            )

        except requests.exceptions.RequestException:
            return service_request_failed()
        
        if handle_unauthorized(response):
            return redirect(url_for("index"))

        if response.status_code == 200:
            return redirect(
                url_for("registration_requests")
            )
        error = get_json_response(response).get(
            "error",
            "Could not accept registration request."
        )

        return render_template(
            "accept_registration_request.html",
            form=form,
            error=error
        )
    
    return render_template(
        "accept_registration_request.html",
        form=form
    )


@app.route("/registration-requests/<int:request_id>/reject",methods=["POST"])
@roles_required("admin")
def reject_registration_request(request_id):

    token = session.get("access_token")

    if not token:
        return redirect(url_for("index"))
    
    try:
        response = requests.post(
            f"{AUTH_SERVICE}/registration-requests/{request_id}/reject",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code == 200:
        return redirect(
            url_for("registration_requests")
        )
    
    error = get_json_response(response).get(
        "error",
        "Could not reject registration request."
    )

    # Ponovo učitamo pending requests da stranica ostane normalna
    try:

        requests_response = requests.get(
            f"{AUTH_SERVICE}/registration-requests",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    registration_requests = []

    if requests_response.status_code == 200:
        registration_requests = get_json_response(requests_response)

    return render_template(
        "registration_requests.html",
        registration_requests=registration_requests,
        error=error
    )


@app.route("/logout", methods=["GET","POST"])
def logout():

    session.clear()
    return redirect(url_for('index'))


@app.route("/my-attendance")
def my_attendance():

    token = session.get("access_token")

    employee_id = session.get("employee_id")

    if not token:
        return redirect(url_for("index"))
    
    try:
        response = requests.get(
            f"{ATTENDANCE_SERVICE_URL}/employee/{employee_id}/attendance",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=3
        )

    except requests.exceptions.RequestException:
        return service_request_failed()
    
    if handle_unauthorized(response):
        return redirect(url_for("index"))
    
    if response.status_code != 200:

        error = get_json_response(response).get("error")

        return render_template(
            "my_attendance.html",
            attendances=[],
            error=error
        )
    
    attendances = get_json_response(response)

    return render_template(
        "my_attendance.html",
        attendances=attendances
    )
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
