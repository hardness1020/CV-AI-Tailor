FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    libpq-dev \
    libmagic1 \
    libmagic-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install Python dependencies with uv
COPY requirements.txt /app/
RUN uv pip install --system --no-cache -r requirements.txt

# Copy project files
COPY . /app/

# Create directory for media files
RUN mkdir -p /app/media

# Create directory for logs
RUN mkdir -p /app/logs

# Set permissions
RUN chmod +x /app/manage.py

# Expose port
EXPOSE 8000

# Default command (overridden in docker-compose.yml)
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]