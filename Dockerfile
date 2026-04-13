# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install uv from the official image (no pip needed)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Dependency layer — cached unless pyproject.toml / uv.lock change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Application source
COPY app/      ./app/
COPY frontend/ ./frontend/

# Backend default; docker-compose overrides CMD for the frontend service
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
