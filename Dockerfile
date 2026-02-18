# Templo Atelier | Studio OS Dockerfile
FROM python:3.13-slim

# Build-time Metadata
LABEL maintainer="Antigravity Studio"
LABEL version="8.0"

# Systems Environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y gcc sqlite3 libsqlite3-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Workspace
COPY . .

# Persistence & Data
RUN mkdir -p projects scenarios/intake_trigger storage


# Networking
EXPOSE 8000

# Start Studio OS (Backend + Dashboard)
CMD ["uvicorn", "src.dashboard_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
