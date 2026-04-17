FROM python:3.10-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir tensorflow-cpu==2.13.1 \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
