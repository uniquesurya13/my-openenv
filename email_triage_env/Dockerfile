FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for security (Huggingface spaces best practice)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app
COPY --chown=user . $HOME/app

# The python openenv module provides standard ways to run. 
# Alternatively, we can run inference.py directly, or start an openenv server.
# According to standard openenv, you run the environment server if it's a Space.
# Default command exposing space on port 7860
CMD ["uvicorn", "openenv.core.server:app", "--host", "0.0.0.0", "--port", "7860"]
