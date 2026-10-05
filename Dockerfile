FROM python:3.13-slim-bookworm


# Set working directory
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /usr/local/bin/

# No system packages needed: every dependency ships a manylinux wheel
# (psycopg2-binary, shapely, numpy, greenlet) for amd64 and arm64.

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
