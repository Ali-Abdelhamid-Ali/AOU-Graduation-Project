FROM python:3.11-slim AS builder

# Prevent Python from writing .pyc files inside the container image.
ENV PYTHONDONTWRITEBYTECODE=1
# Keep stdout/stderr unbuffered so container logs appear immediately.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000"]


