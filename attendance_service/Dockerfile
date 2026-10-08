FROM python:3.14-slim

WORKDIR /app

COPY attendance_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY attendance_service ./attendance_service

CMD ["sh", "-c", "flask --app attendance_service.app db upgrade -d attendance_service/migrations && exec gunicorn --bind 0.0.0.0:${PORT:-5003} --workers 1 attendance_service.app:app"]