FROM python:3.14-slim

WORKDIR /app

COPY auth_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY auth_service ./auth_service

CMD ["sh", "-c", "flask --app auth_service.app db upgrade -d auth_service/migrations && exec gunicorn --bind 0.0.0.0:${PORT:-5004} --workers 1 auth_service.app:app"]