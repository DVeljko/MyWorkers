FROM python:3.14-slim

WORKDIR /app

COPY employee_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY employee_service ./employee_service

CMD ["python", "-m", "employee_service.app"]