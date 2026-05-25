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

# Download models (they go into /root/.local by default)
RUN python -m spacy download en_core_web_md && \
    python -m textblob.download_corpora

RUN mkdir -p /app/models && \
    curl -L -o /app/models/nomic-embed-text-v1.5.Q4_K_M.gguf \
    "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q4_K_M.gguf"

# 2. RUNTIME STAGE
FROM python:3.13-slim
WORKDIR /app

# Install runtime dependencies: libgomp1 (for llama-cpp) + curl (if needed)
RUN apt-get update && apt-get install -y \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy user packages AND fix ownership immediately
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy model files with correct ownership
COPY --from=builder --chown=appuser:appuser /app/models /app/models

# Set environment for user-installed packages
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user before copying application code
USER appuser

# Copy application code (already chowned)
COPY --chown=appuser:appuser . .
RUN mkdir -p log

# (Optional) Verify Spacy model can be loaded at build time
RUN python -c "import spacy; spacy.load('en_core_web_md')" || \
    echo "Spacy model not found – will download at runtime"

EXPOSE 8000
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
