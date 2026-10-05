FROM python:3.14-slim

WORKDIR /app

COPY auth_service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY auth_service ./auth_service

CMD ["python", "-m", "auth_service.app"]