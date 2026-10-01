import os 
from flask_jwt_extended import create_access_token

os.environ['DATABASE_URL'] = "sqlite:///test_employee.db"

import pytest
from datetime import date
from employee_service.app import app
from employee_service.models import db, Employee
import requests

@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()

    yield app.test_client()

    with app.app_context():
        db.session.remove()
        db.drop_all()

def fake_single_department_get(*args, **kwargs):
    class FakeResponse:
        status_code = 200

    return FakeResponse()

def fake_department_not_found(*args, **kwargs):
    class FakeResponse:
        status_code = 404

    return FakeResponse()

def fake_departments_get(*args, **kwargs):
    class FakeResponse:
        status_code = 200

        def json(self):
            return [
                {"id": 1, "name": "IT"},
                {"id": 2, "name": "Design"}
            ]

    return FakeResponse()

def fake_department_service_unavailable(*args, **kwargs):
    raise requests.exceptions.RequestException

def fake_departments_server_error(*args, **kwargs):
    class FakeResponse:
        status_code = 500

    return FakeResponse()


def test_app_exists():
    assert app is not None


def test_get_employee(client):

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1

            }
        )

        new_employee = Employee(
            first_name = "Nemo",
            last_name = "Milanovic",
            email = "nemo123@gmail.com",
            phone = "32242123",
            position = "designer",
            hire_date = date.today(),
            salary = 2000,
            status = "active",
            department_id = 1,
            company_id = 1
        )

        db.session.add(new_employee)
        db.session.commit()


    response = client.get(
        "/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200


def test_get_employee_as_employee(client):

    with app.app_context():
        access_token = create_access_token(
            identity="employee@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1
            }
        )

    response = client.get(
        "/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403
    error = response.get_json().get("error")
    assert error == "Only admin or manager can see all employees"

def test_get_employees_company_isolation(client):

    with app.app_context():

        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1

            }
        )

        new_employee = Employee(
            first_name = "Nemo",
            last_name = "Milanovic",
            email = "nemo123@gmail.com",
            phone = "32242123",
            position = "designer",
            hire_date = date.today(),
            salary = 2000,
            status = "active",
            department_id = 1,
            company_id = 1
        )

        new_employee2 = Employee(
            first_name = "veljko",
            last_name = "dimitrijevic",
            email = "velja123@gmail.com",
            phone = "89749055",
            position = "developer",
            hire_date = date.today(),
            salary = 3000,
            status = "active",
            department_id = 1,
            company_id = 3
        )

        db.session.add(new_employee)
        db.session.add(new_employee2)
        db.session.commit()

    response = client.get(
        "/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["email"] == "nemo123@gmail.com"

def test_get_employees_by_department(client, monkeypatch):

    monkeypatch.setattr(
        "employee_service.app.requests.get",
        fake_single_department_get
    )

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

        new_employee = Employee(
            first_name = "Nemo",
            last_name = "Milanovic",
            email = "nemo123@gmail.com",
            phone = "32242123",
            position = "designer",
            hire_date = date.today(),
            salary = 2000,
            status = "active",
            department_id = 1,
            company_id = 1
        )

        db.session.add(new_employee)
        db.session.commit()
        department_id = new_employee.department_id

    response = client.get(
        f"/employees/{department_id}/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200
    data = response.get_json()

    assert len(data) == 1
    assert data[0]["email"] == "nemo123@gmail.com"


def test_get_employees_by_department_as_employee(client):

    with app.app_context():
        access_token = create_access_token(
            identity="employee@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1
            }
        )

    response = client.get(
        f"/employees/1/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403
    error = response.get_json().get('error')
    assert error == "Only admin or manager can see employees by department"

def test_get_employees_by_department_not_found(client, monkeypatch):

    monkeypatch.setattr("employee_service.app.requests.get", fake_department_not_found)

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims = {
                "role": "admin",
                "company_id": 1
            }
        )

        new_employee = Employee(
            first_name = "Nemo",
            last_name = "Milanovic",
            email = "nemo123@gmail.com",
            phone = "32242123",
            position = "designer",
            hire_date = date.today(),
            salary = 2000,
            status = "active",
            department_id = 333,
            company_id = 1
        )

        db.session.add(new_employee)
        db.session.commit()
        department_id = new_employee.department_id

    response = client.get(
        f"/employees/{department_id}/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 400
    error = response.get_json().get('error')
    assert error == "Department does not exist"


def test_get_employees_department_service_unavailable(client, monkeypatch):

    monkeypatch.setattr("employee_service.app.requests.get", fake_department_service_unavailable)

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )


    response = client.get(
        "/employees/333/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 503

def test_get_single_employee_as_admin(client):

    with app.app_context():

        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

        new_employee = Employee(
            first_name = "Nemo",
            last_name = "Milanovic",
            email = "nemo123@gmail.com",
            phone = "32242123",
            position = "designer",
            hire_date = date.today(),
            salary = 2000,
            status = "active",
            department_id = 1,
            company_id = 1
        )

        db.session.add(new_employee)
        db.session.commit()
        employee_id = new_employee.id


    response = client.get(
        f"/employees/{employee_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200
    data = response.get_json()

    assert data["id"] == employee_id
    assert data["email"] == "nemo123@gmail.com"

def test_get_own_profile_as_employee(client):

    with app.app_context():

        new_employee = Employee(
            first_name = "Nemo",
            last_name = "Milanovic",
            email = "nemo123@gmail.com",
            phone = "32242123",
            position = "designer",
            hire_date = date.today(),
            salary = 2000,
            status = "active",
            department_id = 1,
            company_id = 1
        )

        db.session.add(new_employee)
        db.session.commit()
        employee_id = new_employee.id

        access_token = create_access_token(
            identity="employee@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1,
                "employee_id": employee_id
            }
        )

    response = client.get(
        f"/employees/{employee_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200
    data = response.get_json()

    assert data["id"] == employee_id
    assert data["email"] == "nemo123@gmail.com"


def test_employee_cannot_view_another_employee(client):

    with app.app_context():

        employee_1 = Employee(
            first_name="Nemo",
            last_name="Milanovic",
            email="nemo123@gmail.com",
            phone="32242123",
            position="designer",
            hire_date=date.today(),
            salary=2000,
            status="active",
            department_id=1,
            company_id=1
        )

        employee_2 = Employee(
            first_name="Veljko",
            last_name="Dimitrijevic",
            email="veljko123@gmail.com",
            phone="987654321",
            position="developer",
            hire_date=date.today(),
            salary=3000,
            status="active",
            department_id=1,
            company_id=1
        )

        db.session.add(employee_1)
        db.session.add(employee_2)
        db.session.commit()

        employee_1_id = employee_1.id
        employee_2_id = employee_2.id

        access_token = create_access_token(
            identity="employee@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1,
                "employee_id": employee_1_id
            }
        )

    response = client.get(
        f"/employees/{employee_2_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403

    error = response.get_json().get("error")
    assert error == "You can only view your own profile"


def test_get_single_employee_not_found(client):

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    response = client.get(
        "/employees/999",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 404

    error = response.get_json().get("error")
    assert error == "Employee not found"

def test_get_single_employee_from_another_company(client):

    with app.app_context():

        new_employee = Employee(
            first_name="Nemo",
            last_name="Milanovic",
            email="nemo123@gmail.com",
            phone="32242123",
            position="designer",
            hire_date=date.today(),
            salary=2000,
            status="active",
            department_id=1,
            company_id=2
        )

        db.session.add(new_employee)
        db.session.commit()

        employee_id = new_employee.id

        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    response = client.get(
        f"/employees/{employee_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 404

    error = response.get_json().get("error")
    assert error == "Employee not found"


def test_dashboard_as_admin(client, monkeypatch):

    monkeypatch.setattr("employee_service.app.requests.get", fake_departments_get)

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

        employee1 = Employee(
            first_name = "Nemo",
            last_name = "Milanovic",
            email = "nemo123@gmail.com",
            phone = "12354522444",
            position = "Designer",
            hire_date = date.today(),
            salary = 2000,
            status = "active",
            department_id = 1,
            company_id = 1
        )

        employee2 = Employee(
            first_name = "Velja",
            last_name = "Dimitrijevic",
            email = "velja123@gmail.com",
            phone = "034723408234",
            position = "Developer",
            hire_date = date.today(),
            salary = 2000,
            status = "active",
            department_id = 2,
            company_id = 1
        )

        employee3 = Employee(
            first_name = "Nensi",
            last_name = "Rankovic",
            email = "nensi123@gmail.com",
            phone = "45645675446",
            position = "Frontend Developer",
            hire_date = date.today(),
            salary = 2000,
            status = "active",
            department_id = 2,
            company_id = 1
        )

        db.session.add(employee1)
        db.session.add(employee2)
        db.session.add(employee3)
        db.session.commit()


    response = client.get(
        "/dashboard",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["total_employees"] == 3
    assert data["active_employees"] == 3
    assert data["inactive_employees"] == 0
    assert data["total_departments"] == 2

def test_dashboard_as_employee(client):

    with app.app_context():
        access_token = create_access_token(
            identity="test@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1
            }
        )

    response = client.get(
        "/dashboard",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403
    error = response.get_json().get("error")
    assert error == "Only admin or manager can see dashboard"

def test_dashboard_department_service_unavailable(client, monkeypatch):

    monkeypatch.setattr("employee_service.app.requests.get", fake_department_service_unavailable)

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    response = client.get(
        "/dashboard",
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 503
    error = response.get_json().get("error")
    assert error == "Department service is unavailable"

def test_dashboard_department_service_error(client, monkeypatch):

    monkeypatch.setattr("employee_service.app.requests.get", fake_departments_server_error)

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    response = client.get(
        "/dashboard",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 500
    error = response.get_json().get('error')
    assert error == "Could not load departments"

def test_add_employee_as_admin(client, monkeypatch):

    monkeypatch.setattr("employee_service.app.requests.get", fake_single_department_get)

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "first_name": "Veljko",
            "last_name": "Dimitrijevic",
            "email": "veljko@test.com",
            "phone": "123456789",
            "position": "Backend Developer",
            "hire_date": "2026-10-01",
            "salary": 2500,
            "status": "active",
            "department_id": 1
        }
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["first_name"] == "Veljko"
    assert data["email"] == "veljko@test.com"
    assert data["company_id"] == 1
    assert data["department_id"] == 1

    with app.app_context():
        employee = db.session.scalar(
            db.select(Employee).where(
                Employee.email == "veljko@test.com"
            )
        )

        assert employee is not None
        assert employee.first_name == "Veljko"
        assert employee.company_id == 1

def test_add_employee_as_employee(client):

    with app.app_context():
        access_token = create_access_token(
            identity="employee@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1
            }
        )

    response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403
    error = response.get_json().get("error")
    assert error == "Only admin can add an employee"


def test_add_employee_department_not_found(client, monkeypatch):

    monkeypatch.setattr("employee_service.app.requests.get", fake_department_not_found)

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "first_name": "Veljko",
            "last_name": "Dimitrijevic",
            "email": "veljko@test.com",
            "phone": "123456789",
            "position": "Backend Developer",
            "hire_date": "2026-10-01",
            "salary": 2500,
            "status": "active",
            "department_id": 1
        }

    )

    assert response.status_code == 400
    error = response.get_json().get("error")
    assert error == "Department does not exist"

def test_add_employee_department_service_unavailable(client, monkeypatch):

    monkeypatch.setattr("employee_service.app.requests.get", fake_department_service_unavailable)

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    response = client.post(
        "/employees",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "first_name": "Veljko",
            "last_name": "Dimitrijevic",
            "email": "veljko@test.com",
            "phone": "123456789",
            "position": "Backend Developer",
            "hire_date": "2026-10-01",
            "salary": 2500,
            "status": "active",
            "department_id": 1
        }
    )

    assert response.status_code == 503
    error = response.get_json().get("error")
    assert error == "Department service is unavailable"