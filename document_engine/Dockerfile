# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Prevent Python from writing pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies only if needed (keep image slim)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Default environment variables (override at runtime as needed)
# Use a stable in-container path for easy volume mounts
ENV GEMINI_API_KEY="" \
    PROCESSED_DOCS_OUTPUT_DIR=/data/processed_documents

# Create the output directory and declare it as a volume for persistence
RUN mkdir -p /data/processed_documents
VOLUME ["/data/processed_documents"]

# Copy the application code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Start the API with Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
