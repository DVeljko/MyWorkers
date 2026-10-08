FROM python:3.14-slim

WORKDIR /app

COPY department_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY department_service ./department_service

CMD ["sh", "-c", "flask --app department_service.app db upgrade -d department_service/migrations && exec gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 1 department_service.app:app"]