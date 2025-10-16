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

# Run the application with gunicorn
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:7899", "--workers", "4", "--timeout", "120", "rnb_to_osm:app"]
