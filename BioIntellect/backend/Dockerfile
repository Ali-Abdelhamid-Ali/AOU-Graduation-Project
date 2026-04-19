FROM python:3.11-slim-bookworm

# Prevent Python from writing .pyc files inside the container image.
ENV PYTHONDONTWRITEBYTECODE=1
# Keep stdout/stderr unbuffered so container logs appear immediately.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl for Docker health checks (slim image doesn't include it)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir tensorflow-cpu==2.18.0 \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# --preload loads the app (and AI models) once in the master process before
# forking workers, so each worker shares memory pages instead of re-loading
# the model independently. This prevents RAM × workers overhead.
#
# Workers: 4 handles concurrent non-LLM requests (auth, dashboard, etc.)
# while LLM requests block a single worker per generation.
# Raise GUNICORN_WORKERS via env if deploying on a cloud provider where
# GENERATION_BACKEND=cohere/openai and no model lives in memory.
#
# Timeout: 300 s covers slow ECG/MRI inference. Nginx has its own timeouts
# per-location; this is the gunicorn worker-level safeguard.
CMD ["gunicorn", "main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "1", \
     "-b", "0.0.0.0:8000", \
     "--timeout", "300", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5"]


