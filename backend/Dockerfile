# 1. BUILD STAGE
FROM python:3.13-slim AS builder
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc g++ cmake build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Download models in build stage so they are baked into the layer
RUN python -m spacy download en_core_web_md && \
    python -m textblob.download_corpora

RUN mkdir -p /app/models && \
    curl -L -o /app/models/nomic-embed-text-v1.5.Q4_K_M.gguf \
    "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q4_K_M.gguf"

# 2. RUNTIME STAGE
FROM python:3.13-slim
WORKDIR /app

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && \
    apt-get update && apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Copy only the necessary user-space packages and models
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app/models /app/models

# Create log directory and set permissions before switching user
RUN mkdir -p log && chown -R appuser:appuser /app

# Set permissions and env
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
USER appuser

COPY --chown=appuser:appuser . .

EXPOSE 8000
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
