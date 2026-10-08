FROM python:3.14-slim

WORKDIR /app

COPY employee_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY employee_service ./employee_service

CMD ["sh", "-c", "flask --app employee_service.app db upgrade -d employee_service/migrations && exec gunicorn --bind 0.0.0.0:${PORT:-5002} --workers 1 employee_service.app:app"]