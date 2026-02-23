FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY libs/common/ libs/common/
COPY apps/data/ apps/data/

WORKDIR /app/apps/data
RUN uv sync --frozen --no-cache

EXPOSE 8003

CMD ["uv", "run", "uvicorn", "data.app:app", "--host", "0.0.0.0", "--port", "8003"]
