FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy workspace files needed for the build
COPY pyproject.toml uv.lock ./
COPY libs/common ./libs/common
COPY apps/analytics ./apps/analytics

# Install dependencies (no dev extras)
RUN uv sync --package analytics --no-dev

ENV PYTHONPATH=/app

EXPOSE 8004

CMD ["uv", "run", "--package", "analytics", "uvicorn", "analytics.app:app", \
     "--host", "0.0.0.0", "--port", "8004"]
