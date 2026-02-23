FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY libs/common/ libs/common/
COPY apps/vessel/ apps/vessel/

WORKDIR /app/apps/vessel
RUN uv sync --frozen --no-cache

EXPOSE 8002

CMD ["uv", "run", "uvicorn", "vessel.app:app", "--host", "0.0.0.0", "--port", "8002"]
