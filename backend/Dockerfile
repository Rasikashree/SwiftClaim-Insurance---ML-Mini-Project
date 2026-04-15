# ─── SwiftClaim Backend ───────────────────────────────────────────
# Python 3.11 slim image for a lightweight production container
# ──────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# System deps required by OpenCV headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer-cache friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure the uploads directory exists at runtime
RUN mkdir -p uploads

EXPOSE 5001

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
