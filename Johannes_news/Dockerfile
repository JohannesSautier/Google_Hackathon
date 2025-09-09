FROM python:3.11-slim

# OS deps needed by trafilatura/lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libxml2 libxslt1.1 libxslt1-dev libxml2-dev curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
# If your core file isn't main.py, copy that filename instead.
COPY main.py /app/
COPY server.py /app/

# Cloud Run sets $PORT. Default to 8080 for local runs.
ENV PORT=8080
ENV GEMINI_API_KEY=""
EXPOSE $PORT

# Start FastAPI via uvicorn and bind to $PORT (required by Cloud Run services)
CMD ["sh", "-c", "python -m uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
