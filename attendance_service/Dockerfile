FROM python:3.14-slim

WORKDIR /app

COPY attendance_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY attendance_service ./attendance_service

CMD ["python", "-m", "attendance_service.app"]