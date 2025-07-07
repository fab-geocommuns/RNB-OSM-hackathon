# Build stage
FROM python:3.13-slim-bullseye AS builder

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

RUN groupadd app && useradd --create-home --gid app app

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

COPY uv.lock pyproject.toml ./

RUN uv venv --relocatable
RUN uv sync --frozen --no-install-project
RUN mkdir -p tmp


FROM python:3.13-slim-bullseye

# Create user
RUN groupadd app && useradd --create-home --gid app app
WORKDIR /app

# Copy from build
COPY --chown=app:app . /app
COPY --chown=app:app --from=builder /app/.venv /app/.venv
COPY --chown=app:app --from=builder /app/tmp /app/tmp

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

USER app

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 8 rnb_to_osm:app"]
