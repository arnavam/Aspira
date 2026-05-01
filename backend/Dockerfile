# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cmake \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Download spaCy model and textblob corpora
RUN python -m spacy download en_core_web_md && \
    python -m textblob.download_corpora

# Download embedding model (nomic-embed-text GGUF - ~100MB)
RUN mkdir -p /app/models && \
    curl -L -o /app/models/nomic-embed-text-v1.5.Q4_K_M.gguf \
    "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q4_K_M.gguf"

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies (curl for healthchecks if needed)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/models /app/models

# Update PATH to include user-installed packages
ENV PATH=/root/.local/bin:$PATH

# Copy app code
COPY . .

# Create log directory
RUN mkdir -p log

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
