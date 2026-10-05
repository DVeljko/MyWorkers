FROM python:3.14-slim

WORKDIR /app

COPY department_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY department_service ./department_service

CMD ["python", "-m", "department_service.app"]