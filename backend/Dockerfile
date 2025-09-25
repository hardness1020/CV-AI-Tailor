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

# Copy pyproject.toml and install Python dependencies with uv
COPY pyproject.toml /app/
RUN uv sync --no-dev

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
CMD ["uv", "run", "--frozen", "python", "manage.py", "runserver", "0.0.0.0:8000"]