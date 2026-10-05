import os 

os.environ["DATEBASE_URL"] = "sqlite:///test_department.db"

import pytest
from department_service.app import app
from department_service.models import db, Department
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


def test_get_department(client):


    with app.app_context():


        access_token = create_access_token(
            identity="admin@test.com",
            additional_claims={
                "role": "admin",
                "company_id": 1
            }
        )
        department1 = Department(
            name = "IT",
            company_id = 1
        )

        department2 = Department(
            name = "Design",
            company_id = 1
        )

        department3 = Department(
            name = "Finance",
            company_id = 2
        )

        db.session.add(department1)
        db.session.add(department2)
        db.session.add(department3)

        db.session.commit()

    response = client.get(
        "/departments",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["name"] == "IT"
    assert data[1]["name"] == "Design"
