FROM python:3.13-slim-bullseye


# Set working directory
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /usr/local/bin/

# Install system dependencies for PostGIS and spatial libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    libspatialindex-dev

COPY uv.lock .
COPY pyproject.toml .

# Install dependencies in a virtual environment
RUN uv venv && \
    . .venv/bin/activate && \
    uv sync

# Copy application code
COPY . .

# Create tmp directory for exports
RUN mkdir -p tmp

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"
ENV WEB_CONCURRENCY=4

# Run the application using Uvicorn
CMD ["uvicorn", "rnb_to_osm:app", "--host", "0.0.0.0", "--port", "5000", "--proxy-headers", "--forwarded-allow-ips", "*"]
