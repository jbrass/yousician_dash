FROM python:3.9-slim

WORKDIR /app

COPY . .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8001
CMD ["gunicorn", "app:server", "--bind", "0.0.0.0:8001"]