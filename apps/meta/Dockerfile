FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

# Copy workspace root config
COPY pyproject.toml uv.lock ./

# Copy common lib
COPY libs/common/ libs/common/

# Copy meta service
COPY apps/meta/ apps/meta/

# Install dependencies
WORKDIR /app/apps/meta
RUN uv sync --frozen --no-cache

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "meta.app:app", "--host", "0.0.0.0", "--port", "8000"]
