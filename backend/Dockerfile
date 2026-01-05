FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    cmake \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_md
RUN python -m textblob.download_corpora

# Download embedding model (nomic-embed-text GGUF - ~100MB)
RUN mkdir -p /app/models && \
    curl -L -o /app/models/nomic-embed-text-v1.5.Q4_K_M.gguf \
    "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q4_K_M.gguf"

# Copy app code
COPY . .

# Create log directory
RUN mkdir -p log

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
