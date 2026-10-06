# MyWorkers

MyWorkers is a microservices-based employee management application built with Python and Flask.

The application allows companies to manage employees, departments, attendance, authentication, and employee registration requests while keeping data isolated between different companies.

## Features

- User authentication with JWT
- Multi-company support and data isolation
- Company creation
- Employee registration requests
- Admin approval and rejection of registration requests
- Employee management
- Department management
- Employee attendance tracking
- Check-in and check-out system
- Role-based authorization
- Admin, manager, and employee roles
- Employee profile and personal attendance views
- REST API communication between microservices
- Dockerized services
- Persistent SQLite databases
- Database migrations with Flask-Migrate
- Automated API testing with pytest

## Architecture

MyWorkers uses a microservices architecture consisting of five services:

### Auth Service

Handles:

- User authentication
- JWT generation
- Company creation
- Registration requests
- User roles
- Employee account creation

Runs internally on port `5004`.

### Employee Service

Handles:

- Employee data
- Employee creation
- Employee updates
- Employee deletion
- Employee profiles
- Dashboard employee statistics

Runs internally on port `5002`.

### Department Service

Handles:

- Department creation
- Department updates
- Department deletion
- Department listing
- Company-specific departments

Runs internally on port `5001`.

### Attendance Service

Handles:

- Employee check-in
- Employee check-out
- Attendance history
- Employee-specific attendance
- Attendance management

Runs internally on port `5003`.

### Web Service

Provides the frontend interface and communicates with the backend microservices.

The application is exposed through port `8000`.

## Multi-Company Isolation

MyWorkers supports multiple companies.

Data is isolated using `company_id`, ensuring that users from one company cannot access employees, departments, attendance records, or registration requests belonging to another company.

Authorization and company information are carried through JWT claims.

## Technologies

- Python
- Flask
- Flask-SQLAlchemy
- SQLAlchemy
- Flask-JWT-Extended
- Flask-Login
- Flask-WTF
- Flask-Migrate
- Alembic
- SQLite
- pytest
- Docker
- Docker Compose
- HTML
- CSS
- Bootstrap
- Git
- GitHub

## Testing

The project contains automated API tests for:

- Authentication
- Authorization and permissions
- Employee management
- Department management
- Attendance management
- Registration requests
- Company isolation
- Inter-service communication and error handling

Currently:

```text
112 tests passed
```

Run all tests with:

```bash
python3 -m pytest
```

## Running the Application

### 1. Clone the repository

```bash
git clone https://github.com/DVeljko/MyWorkers.git
cd MyWorkers
```

### 2. Configure environment variables

Each service that requires environment configuration uses its own `.env` file.

Environment files are not included in the repository and should contain the required configuration such as JWT secrets and service URLs.

### 3. Build and start the application

```bash
docker compose up --build
```

Docker Compose will build and start all MyWorkers services.

### 4. Open the application

The web application is available at:

```text
http://localhost:8000
```

## Project Structure

```text
MyWorkers/
│
├── auth_service/
│   ├── app.py
│   ├── models.py
│   ├── migrations/
│   └── Dockerfile
│
├── employee_service/
│   ├── app.py
│   ├── models.py
│   ├── migrations/
│   └── Dockerfile
│
├── department_service/
│   ├── app.py
│   ├── models.py
│   ├── migrations/
│   └── Dockerfile
│
├── attendance_service/
│   ├── app.py
│   ├── models.py
│   ├── migrations/
│   └── Dockerfile
│
├── web_service/
│   ├── app.py
│   ├── templates/
│   ├── static/
│   └── Dockerfile
│
├── tests/
│   ├── test_auth.py
│   ├── test_employee.py
│   ├── test_department.py
│   └── test_attendance.py
│
├── docker-compose.yml
└── README.md
```

## Development

The backend services are structured as Python packages so that the same imports work both during local pytest execution and inside Docker containers.

Example:

```python
from attendance_service.models import Attendance, db
```

Services communicate through HTTP REST APIs while authentication and authorization are handled using JWT tokens.

## Future Improvements

- Continuous Integration with GitHub Actions
- Continuous Deployment
- PostgreSQL support
- Production WSGI server
- Additional automated tests
- Deployment to a cloud platform

## Author

Veljko Dimitrijević

Python Backend Developer