FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Tell TF/PyTorch to use CUDA 12
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-dev python3-pip curl \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir tensorflow[and-cuda]==2.18.0 \
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
     "--timeout", "600", \
     "--graceful-timeout", "60", \
     "--keep-alive", "5", \
     "--preload"]


