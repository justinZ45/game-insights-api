FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true

# Install Poetry
RUN pip install --no-cache-dir "poetry>=2.0.0"

WORKDIR /usr/local/app

# Copy configuration files
COPY pyproject.toml poetry.lock* ./

# Install production dependencies only (Skip dev tools)
RUN poetry install --only main --no-root --no-directory

# Copy application source code
COPY src ./src

# Install project / local package (register "gia")
RUN poetry install --only main

# Use the official python3 distroless image (based on Debian 12)
FROM gcr.io/distroless/python3-debian12:nonroot AS runtime

WORKDIR /usr/local/app

# Copy the entire self-contained virtual environment from the builder
COPY --from=builder /usr/local/app/.venv /usr/local/app/.venv
COPY --from=builder /usr/local/app/src /usr/local/app/src

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Put the venv's active python interpreter first in PATH
    PATH="/usr/local/app/.venv/bin:$PATH" \
    # Point Python to source code directory
    PYTHONPATH="/usr/local/app"

EXPOSE 8000

# Invoke uvicorn inside venv
ENTRYPOINT ["/usr/local/app/.venv/bin/uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]