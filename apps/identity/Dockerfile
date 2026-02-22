FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY libs/common/ libs/common/
COPY apps/identity/ apps/identity/

WORKDIR /app/apps/identity
RUN uv sync --frozen --no-cache

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "identity.app:app", "--host", "0.0.0.0", "--port", "8001"]
