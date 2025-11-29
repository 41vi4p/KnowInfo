FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip

# Install Python dependencies with retry logic and increased timeout
RUN pip install  --timeout 1000 --retries 5 -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/vector_db /app/data/knowledge_base /app/data/models

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
