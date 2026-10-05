import os

os.environ["DATABASE_URL"] = "sqlite:///test_attendance.db"

import pytest
import requests
from datetime import datetime

from attendance_service.app import app
from attendance_service.models import db, Attendance
from flask_jwt_extended import create_access_token


@pytest.fixture
def client():

    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()

    yield app.test_client()

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_app_exists():
    assert app is not None

def test_check_in_as_admin(client, monkeypatch):

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    class FakeResponse:
        status_code = 200

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "attendance_service.app.requests.get",
        fake_get
    )

    response = client.post(
        "/attendance/5",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["employee_id"] == 5
    assert data["company_id"] == 1

    with app.app_context():
        attendance = db.session.scalar(
            db.select(Attendance).where(
                Attendance.employee_id == 5,
                Attendance.company_id == 1
            )
        )

        assert attendance is not None
        assert attendance.employee_id == 5
        assert attendance.company_id == 1
        assert attendance.arrival_time is not None
        assert attendance.departure_time is None


def test_check_in_employee_himself(client, monkeypatch):

    with app.app_context():
        access_token = create_access_token(
            identity="employee@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1,
                "employee_id": 5
            }
        )

    class FakeResponse:
        status_code = 200

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "attendance_service.app.requests.get",
        fake_get
    )

    response = client.post(
        "/attendance/5",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["employee_id"] == 5
    assert data["company_id"] == 1

    with app.app_context():
        attendance = db.session.scalar(
            db.select(Attendance).where(
                Attendance.employee_id == 5,
                Attendance.company_id == 1
            )
        )

        assert attendance is not None
        assert attendance.arrival_time is not None
        assert attendance.departure_time is None


def test_check_in_another_employee(client):

    with app.app_context():
        access_token = create_access_token(
            identity="employee@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1,
                "employee_id": 5
            }
        )

    response = client.post(
        "/attendance/6",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403

    error = response.get_json().get("error")

    assert error == "You can only check in yourself"

def test_check_in_employee_already_checked_in(client, monkeypatch):

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

        attendance = Attendance(
            employee_id=5,
            company_id=1,
            arrival_time=datetime.now()
        )

        db.session.add(attendance)
        db.session.commit()

    class FakeResponse:
        status_code = 200

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "attendance_service.app.requests.get",
        fake_get
    )

    response = client.post(
        "/attendance/5",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 409

    error = response.get_json().get("error")

    assert error == "Employee is already checked in"



def test_check_in_employee_not_found(client, monkeypatch):

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    class FakeResponse:
        status_code = 404

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "attendance_service.app.requests.get",
        fake_get
    )

    response = client.post(
        "/attendance/999",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 400

    error = response.get_json().get("error")

    assert error == "Employee does not exist"


def test_check_in_employee_service_unavailable(client, monkeypatch):

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    def fake_get(*args, **kwargs):
        raise requests.exceptions.RequestException

    monkeypatch.setattr(
        "attendance_service.app.requests.get",
        fake_get
    )

    response = client.post(
        "/attendance/5",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 503

    error = response.get_json().get("error")

    assert error == "Employee service is unavailable"

def test_check_out_as_admin(client, monkeypatch):

    with app.app_context():
        attendance = Attendance(
            employee_id=5,
            company_id=1,
            arrival_time=datetime.now()
        )

        db.session.add(attendance)
        db.session.commit()

        attendance_id = attendance.id

        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    class FakeResponse:
        status_code = 200

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "attendance_service.app.requests.get",
        fake_get
    )

    response = client.patch(
        "/attendance/5",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["employee_id"] == 5
    assert data["company_id"] == 1
    assert data["departure_time"] is not None

    with app.app_context():
        attendance = db.session.get(
            Attendance,
            attendance_id
        )

        assert attendance is not None
        assert attendance.departure_time is not None

def test_check_out_employee_himself(client, monkeypatch):

    with app.app_context():
        attendance = Attendance(
            employee_id=5,
            company_id=1,
            arrival_time=datetime.now()
        )

        db.session.add(attendance)
        db.session.commit()

        attendance_id = attendance.id

        access_token = create_access_token(
            identity="employee@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1,
                "employee_id": 5
            }
        )

    class FakeResponse:
        status_code = 200

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "attendance_service.app.requests.get",
        fake_get
    )

    response = client.patch(
        "/attendance/5",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["employee_id"] == 5
    assert data["company_id"] == 1
    assert data["departure_time"] is not None

    with app.app_context():
        attendance = db.session.get(
            Attendance,
            attendance_id
        )

        assert attendance is not None
        assert attendance.departure_time is not None


def test_check_out_another_employee(client):

    with app.app_context():
        access_token = create_access_token(
            identity="employee@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1,
                "employee_id": 5
            }
        )

    response = client.patch(
        "/attendance/6",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403

    error = response.get_json().get("error")

    assert error == "You can only check out yourself"

def test_check_out_employee_not_checked_in(client, monkeypatch):

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    class FakeResponse:
        status_code = 200

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "attendance_service.app.requests.get",
        fake_get
    )

    response = client.patch(
        "/attendance/5",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 409

    error = response.get_json().get("error")

    assert error == "Employee is not checked in"


def test_check_out_employee_not_found(client, monkeypatch):

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    class FakeResponse:
        status_code = 404

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "attendance_service.app.requests.get",
        fake_get
    )

    response = client.patch(
        "/attendance/999",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 400

    error = response.get_json().get("error")

    assert error == "Employee does not exist"


def test_check_out_employee_service_unavailable(client, monkeypatch):

    with app.app_context():
        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    def fake_get(*args, **kwargs):
        raise requests.exceptions.RequestException

    monkeypatch.setattr(
        "attendance_service.app.requests.get",
        fake_get
    )

    response = client.patch(
        "/attendance/5",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 503

    error = response.get_json().get("error")

    assert error == "Employee service is unavailable"


def test_get_all_attendance_as_admin(client):

    with app.app_context():
        attendance1 = Attendance(
            employee_id=5,
            company_id=1,
            arrival_time=datetime.now()
        )

        attendance2 = Attendance(
            employee_id=6,
            company_id=1,
            arrival_time=datetime.now()
        )

        db.session.add_all([
            attendance1,
            attendance2
        ])
        db.session.commit()

        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    response = client.get(
        "/attendance",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 2
    assert data[0]["employee_id"] == 5
    assert data[1]["employee_id"] == 6


def test_get_all_attendance_as_manager(client):

    with app.app_context():
        attendance = Attendance(
            employee_id=5,
            company_id=1,
            arrival_time=datetime.now()
        )

        db.session.add(attendance)
        db.session.commit()

        access_token = create_access_token(
            identity="manager@test.com",
            additional_claims={
                "role": "manager",
                "company_id": 1
            }
        )

    response = client.get(
        "/attendance",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 1
    assert data[0]["employee_id"] == 5
    assert data[0]["company_id"] == 1


def test_get_all_attendance_as_employee(client):

    with app.app_context():
        access_token = create_access_token(
            identity="employee@test.com",
            additional_claims={
                "role": "employee",
                "company_id": 1,
                "employee_id": 5
            }
        )

    response = client.get(
        "/attendance",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403

    error = response.get_json().get("error")

    assert error == "Only admin or manager can see all attendance"


def test_get_all_attendance_company_isolation(client):

    with app.app_context():
        attendance_company_1 = Attendance(
            employee_id=5,
            company_id=1,
            arrival_time=datetime.now()
        )

        attendance_company_2 = Attendance(
            employee_id=10,
            company_id=2,
            arrival_time=datetime.now()
        )

        db.session.add_all([
            attendance_company_1,
            attendance_company_2
        ])
        db.session.commit()

        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )

    response = client.get(
        "/attendance",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 1
    assert data[0]["employee_id"] == 5
    assert data[0]["company_id"] == 1