FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Create __init__.py files for package imports
RUN touch tasks/__init__.py graders/__init__.py

# HuggingFace Spaces runs as non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (HF Spaces uses 7860)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:7860/health')"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
