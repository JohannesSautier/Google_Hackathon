# small, boring, reliable
FROM python:3.10-slim

# avoid pip noise & speed up
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# install deps first (better layer caching)
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir --root-user-action ignore -r requirements.txt

# copy the app
COPY app.py .

# Cloud Run listens on $PORT (defaults to 8080 locally)
ENV PORT=8080

# use gunicorn in containers
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 2 app:app
