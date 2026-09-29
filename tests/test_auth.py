import os

os.environ["DATABASE_URL"] = "sqlite:///test_auth.db"

import pytest

from auth_service.app import app, User, generate_password_hash, Company, RegistrationRequest
from auth_service.models import db


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()

    yield app.test_client()

    with app.app_context():
        db.session.remove()
        db.drop_all()


def fake_post(*args, **kwargs):
    class FakeResponse:
        status_code = 201

        def json(self):
            return {"id": 10}

    return FakeResponse()


def fake_get(*args, **kwargs):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "id": 10,
                "email": "employee@test.com"
            }

    return FakeResponse()

def fake_get_wrong_email(*args, **kwargs):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "id": 10,
                "email": "someone_else@test.com"
            }

    return FakeResponse()


def fake_get_employee_not_found(*args, **kwargs):
    class FakeResponse:
        status_code = 404

        def json(self):
            return {"error": "Employee not found"}

    return FakeResponse()

def test_app_exists():
    assert app is not None


def test_login_wrong_password(client):

    user = User(
        company_id= 1,
        email = "test@test.com",
        password =  generate_password_hash("test123"),
        role = "employee",
        employee_id = 1,
    )

    with app.app_context():
        db.session.add(user)
        db.session.commit()

    response = client.post("/login", json={
        "email": "test@test.com",
        "password": "test"
    })

    assert response.status_code == 401
    error = response.get_json().get('error')
    assert error == "Wrong password"



def test_successful_login(client):
        
    user = User(
        company_id= 1,
        email = "test@test.com",
        password =  generate_password_hash("test123"),
        role = "employee",
        employee_id = 1,
    )

    with app.app_context():
        db.session.add(user)
        db.session.commit()

    response = client.post("/login", json={
        "email": "test@test.com",
        "password": "test123"
    })

    assert response.status_code == 200
    data = response.get_json()

    access_token = data.get('access_token')
    role = data.get('role')
    employee_id = data.get('employee_id')

    assert access_token
    assert role == "employee"
    assert employee_id == 1


def test_login_wrong_email(client):

    user = User(
        company_id= 1,
        email = "test@test.com",
        password =  generate_password_hash("test123"),
        role = "employee",
        employee_id = 1,
    )

    with app.app_context():
        db.session.add(user)
        db.session.commit()

    response = client.post("/login", json={
        "email": "test@proba.com",
        "password": "test123"
    })

    assert response.status_code == 401
    error = response.get_json().get('error')
    assert error == "There is no employee with this email"


def test_register_company_success(client):

    response = client.post("/register", json={
        "email": "nemo123@gmail.com",
        "password": "jasamnemo123",
        "confirm_password": "jasamnemo123",
        "company_name": "nemoslav company",
        "owner_first_name": "nemanja",
        "owner_last_name": "milanovic"
    })

    data = response.get_json()
    success = data['success']
    assert response.status_code == 201
    assert success == "Company and admin account created successfully"

    with app.app_context():
        company = db.session.scalar(db.select(Company).where(Company.name == "nemoslav company"))
        user = db.session.scalar(db.select(User).where(User.email == "nemo123@gmail.com"))

    assert company is not None
    assert user is not None
    role = user.role
    assert role == "admin"

def test_register_passwords_do_not_match(client):

    response = client.post("/register", json={
        "email": "nemo123@gmail.com",
        "password": "jasamnemo123",
        "confirm_password": "jasamnemo",
        "company_name": "nemoslav company",
        "owner_first_name": "nemanja",
        "owner_last_name": "milanovic"
    })

    error = response.get_json().get('error')
    assert response.status_code == 400
    assert error == "Password do not match"

def test_register_company_already_exists(client):

    response = client.post("/register", json={
        "email": "nemo123@gmail.com",
        "password": "jasamnemo123",
        "confirm_password": "jasamnemo123",
        "company_name": "nemoslav company",
        "owner_first_name": "nemanja",
        "owner_last_name": "milanovic"
    })

    assert response.status_code == 201

    new_response = client.post("/register", json={
        "email": "velja123@gmail.com",
        "password": "jasamnemo123",
        "confirm_password": "jasamnemo123",
        "company_name": "nemoslav company",
        "owner_first_name": "veljko",
        "owner_last_name": "dimitrijevic"
    })

    error = new_response.get_json().get('error')
    assert new_response.status_code == 409
    assert error == "This company already exists!"


def test_register_email_already_exists(client):

    response = client.post("/register", json={
        "email": "nemo123@gmail.com",
        "password": "jasamnemo123",
        "confirm_password": "jasamnemo123",
        "company_name": "nemoslav company",
        "owner_first_name": "nemanja",
        "owner_last_name": "milanovic"
    })

    assert response.status_code == 201

    new_response = client.post("/register", json={
        "email": "nemo123@gmail.com",
        "password": "jasamnemo123",
        "confirm_password": "jasamnemo123",
        "company_name": "velja company",
        "owner_first_name": "veljko",
        "owner_last_name": "dimitrijevic"
    })

    error = new_response.get_json().get('error')
    assert new_response.status_code == 409
    assert error == "Employee with this email already exists"


def test_register_employee_success(client):              

    company = Company(
        name = "IT Web",
        owner_first_name = "Veljko",
        owner_last_name = "Dimitrijevic"
    )

    with app.app_context():
        db.session.add(company)
        db.session.commit()
        company_id = company.id

    response = client.post(
        "/register-employee",
        json={
            "email": "nemo123@gmail.com",
            "password": "jasamnemo123",
            "confirm_password": "jasamnemo123",
            "first_name": "nemanja",
            "last_name": "milanovic",
            "company_id": company_id
        }

    )

    assert response.status_code == 201

    with app.app_context():
        request_exists = db.session.scalar(db.select(RegistrationRequest).where(RegistrationRequest.email == "nemo123@gmail.com"))

    assert request_exists is not None


def test_register_employee_company_not_found(client):

    response = client.post(
        "/register-employee",
        json={
            "email": "nemo123@gmail.com",
            "password": "jasamnemo123",
            "confirm_password": "jasamnemo123",
            "first_name": "nemanja",
            "last_name": "milanovic",
            "company_id": 99
        }

    )

    assert response.status_code == 404
    error = response.get_json().get("error")
    assert error == "There is no company with that ID"



def test_registration_request_already_exists(client):


    company = Company(
        name = "IT Web",
        owner_first_name = "Veljko",
        owner_last_name = "Dimitrijevic"
    )

    with app.app_context():
        db.session.add(company)
        db.session.commit()
        company_id = company.id

    response = client.post(
        "/register-employee",
        json={
            "email": "nemo123@gmail.com",
            "password": "jasamnemo123",
            "confirm_password": "jasamnemo123",
            "first_name": "nemanja",
            "last_name": "milanovic",
            "company_id": company_id
        }

    )

    assert response.status_code == 201

    new_response = client.post(
        "/register-employee",
        json={
            "email": "nemo123@gmail.com",
            "password": "jasamnemo123",
            "confirm_password": "jasamnemo123",
            "first_name": "nemanja",
            "last_name": "milanovic",
            "company_id": company_id
        }

    )
    error = new_response.get_json().get("error")
    assert new_response.status_code == 409
    assert error == "Registration request already exists" 


def test_register_employee_passwords_do_not_match(client):

    response = client.post(
        "/register-employee",
        json={
            "email": "nemo123@gmail.com",
            "password": "jasamnemo123",
            "confirm_password": "jasamnemo",
            "first_name": "nemanja",
            "last_name": "milanovic",
            "company_id": 200
        }

    )

    error = response.get_json().get('error')
    assert response.status_code == 400
    assert error == "Password do not match"


def test_register_employee_email_already_exists(client):

    user = User(
        company_id = 1,
        email="nemo123@gmail.com",
        password="jasamnemo123",
        role="employee",
        employee_id=1
    )

    with app.app_context():
        db.session.add(user)
        db.session.commit()

    response = client.post("/register-employee", json={
        "email": "nemo123@gmail.com",
        "password": "jasamnemo123",
        "confirm_password": "jasamnemo123",
        "first_name": "nemanja",
        "last_name": "milanovic",
        "company_id": 1
    })

    error = response.get_json().get("error")
    assert response.status_code == 409
    assert error == "Employee with this email already exists"

def test_get_registration_requests_admin_success(client):

    user = User(
        company_id = 1,
        email = "dveljko3@gmail.com",
        password = generate_password_hash("jasamveljko123"),
        role="admin",
        employee_id = 1
    )

    with app.app_context():
        db.session.add(user)
        db.session.commit()

    login_response = client.post("/login", json={
        "email": "dveljko3@gmail.com",
        "password": "jasamveljko123"
    })

    assert login_response.status_code == 200
    data = login_response.get_json()
    access_token = data['access_token']

    response = client.get(
        f"/registration-requests",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200

def test_get_registration_requests_non_admin_forbidden(client):

    user = User(
        company_id = 1,
        email = "dveljko3@gmail.com",
        password = generate_password_hash("jasamveljko123"),
        role="employee",
        employee_id = 1
    )

    with app.app_context():
        db.session.add(user)
        db.session.commit()

    login_response = client.post("/login", json={
        "email": "dveljko3@gmail.com",
        "password": "jasamveljko123"
    })

    assert login_response.status_code == 200
    data = login_response.get_json()
    access_token = data['access_token']

    response = client.get(
        f"/registration-requests",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    error = response.get_json().get('error')
    assert response.status_code == 403
    assert error == "Admin access required"


def test_get_registration_requests_only_own_company(client):

    user = User(
        company_id = 1,
        email = "dveljko3@gmail.com",
        password = generate_password_hash("jasamveljko123"),
        role="admin",
        employee_id = 1
    )

    employee1 = RegistrationRequest(
        company_id = 1,
        first_name = "nevena",
        last_name = "rankovic",
        email = "nevena456@gmail.com",
        password = "jasamnevena123"
    )

    employee2 = RegistrationRequest(
        company_id = 2,
        first_name = "nemanja",
        last_name = "milanovic",
        email = "nemo123@gmail.com",
        password = "jasamnemo123"
    )

    with app.app_context():
        db.session.add(user)
        db.session.add(employee1)
        db.session.add(employee2)
        db.session.commit()

    login_response = client.post(
        "/login",
        json={
            "email": "dveljko3@gmail.com",
            "password": "jasamveljko123"
        }
    )

    assert login_response.status_code == 200
    data = login_response.get_json()
    access_token = data['access_token']

    response = client.get(
        "registration-requests",
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
    )

    data = response.get_json()
    email = data[0]['email']

    assert email == "nevena456@gmail.com"
    assert response.status_code == 200
    assert len(data) == 1


def test_reject_registration_request_success(client):

    user = User(
        company_id = 1,
        email = "dveljko3@gmail.com",
        password = generate_password_hash("jasamveljko123"),
        role="admin",
        employee_id = 1
    )

    employee1 = RegistrationRequest(
        company_id = 1,
        first_name = "nevena",
        last_name = "rankovic",
        email = "nevena456@gmail.com",
        password = "jasamnevena123"
    )

    with app.app_context():
        db.session.add(user)
        db.session.add(employee1)
        db.session.commit()

        request_id = employee1.id


    
    login_response = client.post(
        "/login",
        json={
            "email": "dveljko3@gmail.com",
            "password": "jasamveljko123"
        }
    )

    data = login_response.get_json()
    access_token = data['access_token']

    assert login_response.status_code == 200

    reject_response = client.post(
        f"/registration-requests/{request_id}/reject",
        headers={
            "Authorization": f"Bearer {access_token}",
        }
    )

    assert reject_response.status_code == 200
    data = reject_response.get_json()
    success = data['success']
    assert success == "Registration request rejected"


def test_reject_registration_request_non_admin_forbidden(client):

    user = User(
        company_id = 1,
        email = "dveljko3@gmail.com",
        password = generate_password_hash("jasamveljko123"),
        role="employee",
        employee_id = 1
    )

    employee1 = RegistrationRequest(
        company_id = 1,
        first_name = "nevena",
        last_name = "rankovic",
        email = "nevena456@gmail.com",
        password = "jasamnevena123"
    )

    with app.app_context():
        db.session.add(user)
        db.session.add(employee1)
        db.session.commit()

        request_id = employee1.id

    login_response = client.post(
        "/login",
        json={
            "email": "dveljko3@gmail.com",
            "password": "jasamveljko123"
        }
    )

    data = login_response.get_json()
    access_token = data['access_token']

    assert login_response.status_code == 200

    reject_response = client.post(
        f"/registration-requests/{request_id}/reject",
        headers={
            "Authorization": f"Bearer {access_token}",
        }
    )

    assert reject_response.status_code == 403
    error = reject_response.get_json().get('error')
    assert error == "Admin only"


def test_reject_registration_request_wrong_company_forbidden(client):

    user = User(
        company_id = 1,
        email = "dveljko3@gmail.com",
        password = generate_password_hash("jasamveljko123"),
        role="admin",
        employee_id = 1
    )

    employee1 = RegistrationRequest(
        company_id = 3,
        first_name = "nevena",
        last_name = "rankovic",
        email = "nevena456@gmail.com",
        password = "jasamnevena123"
    )

    with app.app_context():
        db.session.add(user)
        db.session.add(employee1)
        db.session.commit()

        request_id = employee1.id


    
    login_response = client.post(
        "/login",
        json={
            "email": "dveljko3@gmail.com",
            "password": "jasamveljko123"
        }
    )

    data = login_response.get_json()
    access_token = data['access_token']

    assert login_response.status_code == 200

    reject_response = client.post(
        f"/registration-requests/{request_id}/reject",
        headers={
            "Authorization": f"Bearer {access_token}",
        }
    )

    assert reject_response.status_code == 403
    error = reject_response.get_json().get('error')
    assert error == "This request does not belong to your company"

def test_reject_registration_request_not_pending(client):

    user = User(
        company_id=1,
        email="dveljko3@gmail.com",
        password=generate_password_hash("jasamveljko123"),
        role="admin",
        employee_id=1
    )

    employee1 = RegistrationRequest(
        company_id=1,
        first_name="nevena",
        last_name="rankovic",
        email="nevena456@gmail.com",
        password="jasamnevena123",
        status="rejected"
    )

    with app.app_context():
        db.session.add(user)
        db.session.add(employee1)
        db.session.commit()

        request_id = employee1.id

    login_response = client.post(
        "/login",
        json={
            "email": "dveljko3@gmail.com",
            "password": "jasamveljko123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    reject_response = client.post(
        f"/registration-requests/{request_id}/reject",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert reject_response.status_code == 400

    error = reject_response.get_json()["error"]
    assert error == "Registration request is not pending"


def test_reject_registration_request_not_found(client):

    user = User(
        company_id=1,
        email="dveljko3@gmail.com",
        password=generate_password_hash("jasamveljko123"),
        role="admin",
        employee_id=1
    )

    with app.app_context():
        db.session.add(user)
        db.session.commit()

    login_response = client.post(
        "/login",
        json={
            "email": "dveljko3@gmail.com",
            "password": "jasamveljko123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    reject_response = client.post(
        "/registration-requests/999/reject",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert reject_response.status_code == 404

    error = reject_response.get_json()["error"]
    assert error == "Registration request not found"

def test_accept_registration_request_success(client, monkeypatch):

    user = User(
        company_id=1,
        email="dveljko3@gmail.com",
        password=generate_password_hash("jasamveljko123"),
        role="admin",
        employee_id=1
    )

    registration_request = RegistrationRequest(
        company_id=1,
        first_name="nevena",
        last_name="rankovic",
        email="nevena456@gmail.com",
        password=generate_password_hash("jasamnevena123")
    )

    with app.app_context():
        db.session.add(user)
        db.session.add(registration_request)
        db.session.commit()

        request_id = registration_request.id

    monkeypatch.setattr(
        "auth_service.app.requests.post",
        fake_post
    )

    login_response = client.post(
        "/login",
        json={
            "email": "dveljko3@gmail.com",
            "password": "jasamveljko123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    accept_response = client.post(
        f"/registration-requests/{request_id}/accept",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "phone": "065123456",
            "position": "Backend Developer",
            "hire_date": "2026-09-29",
            "salary": 1500,
            "department_id": 1
        }
    )

    assert accept_response.status_code == 200

    data = accept_response.get_json()

    assert data["success"] == "Registration request accepted"
    assert data["employee_id"] == 10


    with app.app_context():
        registration_request = db.session.get(
            RegistrationRequest,
            request_id
        )

        assert registration_request.status == "accepted"

        new_user = db.session.scalar(
            db.select(User).where(
                User.email == "nevena456@gmail.com"
            )
        )

        assert new_user is not None
        assert new_user.employee_id == 10
        assert new_user.role == "employee"

def test_accept_registration_request_wrong_company_forbidden(client):

    user = User(
        company_id=1,
        email="dveljko3@gmail.com",
        password=generate_password_hash("jasamveljko123"),
        role="admin",
        employee_id=1
    )

    registration_request = RegistrationRequest(
        company_id=2,
        first_name="nevena",
        last_name="rankovic",
        email="nevena456@gmail.com",
        password=generate_password_hash("jasamnevena123")
    )

    with app.app_context():
        db.session.add(user)
        db.session.add(registration_request)
        db.session.commit()

        request_id = registration_request.id

    login_response = client.post(
        "/login",
        json={
            "email": "dveljko3@gmail.com",
            "password": "jasamveljko123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    accept_response = client.post(
        f"/registration-requests/{request_id}/accept",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "phone": "065123456",
            "position": "Backend Developer",
            "hire_date": "2026-09-29",
            "salary": 1500,
            "department_id": 1
        }
    )

    assert accept_response.status_code == 403

    data = accept_response.get_json()

    assert data["error"] == "This request does not belong to your company"


def test_accept_registration_request_not_pending(client):

    user = User(
        company_id=1,
        email="dveljko3@gmail.com",
        password=generate_password_hash("jasamveljko123"),
        role="admin",
        employee_id=1
    )

    registration_request = RegistrationRequest(
        company_id=1,
        first_name="nevena",
        last_name="rankovic",
        email="nevena456@gmail.com",
        password=generate_password_hash("jasamnevena123"),
        status="rejected"
    )

    with app.app_context():
        db.session.add(user)
        db.session.add(registration_request)
        db.session.commit()

        request_id = registration_request.id

    login_response = client.post(
        "/login",
        json={
            "email": "dveljko3@gmail.com",
            "password": "jasamveljko123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    accept_response = client.post(
        f"/registration-requests/{request_id}/accept",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={}
    )

    assert accept_response.status_code == 400

    data = accept_response.get_json()

    assert data["error"] == "Registration request is not pending"


def test_update_user_role_success(client):

    admin = User(
        company_id=1,
        email="admin@test.com",
        password=generate_password_hash("admin123"),
        role="admin",
        employee_id=1
    )

    employee = User(
        company_id=1,
        email="employee@test.com",
        password=generate_password_hash("employee123"),
        role="employee",
        employee_id=2
    )

    with app.app_context():
        db.session.add(admin)
        db.session.add(employee)
        db.session.commit()

        employee_user_id = employee.id

    login_response = client.post(
        "/login",
        json={
            "email": "admin@test.com",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/users/{employee_user_id}/role",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "role": "manager"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["role"] == "manager"

    with app.app_context():
        updated_user = db.session.get(User, employee_user_id)

        assert updated_user.role == "manager"


def test_update_user_role_non_admin_forbidden(client):

    employee1 = User(
        company_id=1,
        email="employee1@test.com",
        password=generate_password_hash("employee123"),
        role="employee",
        employee_id=1
    )

    employee2 = User(
        company_id=1,
        email="employee2@test.com",
        password=generate_password_hash("employee456"),
        role="employee",
        employee_id=2
    )

    with app.app_context():
        db.session.add(employee1)
        db.session.add(employee2)
        db.session.commit()

        employee2_id = employee2.id

    login_response = client.post(
        "/login",
        json={
            "email": "employee1@test.com",
            "password": "employee123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/users/{employee2_id}/role",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "role": "manager"
        }
    )

    assert response.status_code == 403

    data = response.get_json()

    assert data["error"] == "Admin access required"


def test_update_user_role_invalid_role(client):

    admin = User(
        company_id=1,
        email="admin@test.com",
        password=generate_password_hash("admin123"),
        role="admin",
        employee_id=1
    )

    employee = User(
        company_id=1,
        email="employee@test.com",
        password=generate_password_hash("employee123"),
        role="employee",
        employee_id=2
    )

    with app.app_context():
        db.session.add(admin)
        db.session.add(employee)
        db.session.commit()

        employee_id = employee.id

    login_response = client.post(
        "/login",
        json={
            "email": "admin@test.com",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/users/{employee_id}/role",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "role": "superadmin"
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Role is not valid"


def test_update_user_role_wrong_company(client):

    admin = User(
        company_id=1,
        email="admin@test.com",
        password=generate_password_hash("admin123"),
        role="admin",
        employee_id=1
    )

    employee = User(
        company_id=2,
        email="employee@test.com",
        password=generate_password_hash("employee123"),
        role="employee",
        employee_id=2
    )

    with app.app_context():
        db.session.add(admin)
        db.session.add(employee)
        db.session.commit()

        employee_id = employee.id

    login_response = client.post(
        "/login",
        json={
            "email": "admin@test.com",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/users/{employee_id}/role",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "role": "manager"
        }
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == "User not found"


def test_link_user_to_employee_success(client, monkeypatch):

    admin = User(
        company_id=1,
        email="admin@test.com",
        password=generate_password_hash("admin123"),
        role="admin",
        employee_id=1
    )

    user = User(
        company_id=1,
        email="employee@test.com",
        password=generate_password_hash("employee123"),
        role="employee",
        employee_id=None
    )

    with app.app_context():
        db.session.add(admin)
        db.session.add(user)
        db.session.commit()

        user_id = user.id

    monkeypatch.setattr(
        "auth_service.app.requests.get",
        fake_get
    )

    login_response = client.post(
        "/login",
        json={
            "email": "admin@test.com",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/users/{user_id}/employee",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "employee_id": 10
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] == "User linked to employee successfully"

    with app.app_context():
        updated_user = db.session.get(User, user_id)

        assert updated_user.employee_id == 10


def test_link_user_to_employee_email_mismatch(client, monkeypatch):

    admin = User(
        company_id=1,
        email="admin@test.com",
        password=generate_password_hash("admin123"),
        role="admin",
        employee_id=1
    )

    user = User(
        company_id=1,
        email="employee@test.com",
        password=generate_password_hash("employee123"),
        role="employee",
        employee_id=None
    )

    with app.app_context():
        db.session.add(admin)
        db.session.add(user)
        db.session.commit()

        user_id = user.id

    monkeypatch.setattr(
        "auth_service.app.requests.get",
        fake_get_wrong_email
    )

    login_response = client.post(
        "/login",
        json={
            "email": "admin@test.com",
            "password": "admin123"
        }
    )

    access_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/users/{user_id}/employee",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "employee_id": 10
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "User email does not match employee email"


def test_link_user_to_employee_not_found(client, monkeypatch):

    admin = User(
        company_id=1,
        email="admin@test.com",
        password=generate_password_hash("admin123"),
        role="admin",
        employee_id=1
    )

    user = User(
        company_id=1,
        email="employee@test.com",
        password=generate_password_hash("employee123"),
        role="employee",
        employee_id=None
    )

    with app.app_context():
        db.session.add(admin)
        db.session.add(user)
        db.session.commit()

        user_id = user.id

    monkeypatch.setattr(
        "auth_service.app.requests.get",
        fake_get_employee_not_found
    )

    login_response = client.post(
        "/login",
        json={
            "email": "admin@test.com",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/users/{user_id}/employee",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "employee_id": 999
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Employee does not exist"


def test_link_user_to_employee_non_admin_forbidden(client):

    employee = User(
        company_id=1,
        email="employee@test.com",
        password=generate_password_hash("employee123"),
        role="employee",
        employee_id=1
    )

    target_user = User(
        company_id=1,
        email="target@test.com",
        password=generate_password_hash("target123"),
        role="employee",
        employee_id=None
    )

    with app.app_context():
        db.session.add(employee)
        db.session.add(target_user)
        db.session.commit()

        target_user_id = target_user.id

    login_response = client.post(
        "/login",
        json={
            "email": "employee@test.com",
            "password": "employee123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.get_json()["access_token"]

    response = client.patch(
        f"/users/{target_user_id}/employee",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "employee_id": 10
        }
    )

    assert response.status_code == 403

    data = response.get_json()

    assert data["error"] == "Admin access required"