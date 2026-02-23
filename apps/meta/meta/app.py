"""FastAPI application entry point for the meta service."""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from common.exceptions import setup_exception_handlers
from common.logging import setup_logging
from common.models import Base
from common.schemas import ResponseModel
from fastapi import FastAPI, Request
from sqlalchemy import text

from meta.config import settings
from meta.database import engine
from meta.router import router

logger = logging.getLogger(__name__)

_SEED_SQL = Path(__file__).parent / "seed.sql"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging("meta", settings.log_level)
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        if not conn.execute(text("SELECT 1 FROM fuel_type LIMIT 1")).first():
            for stmt in _SEED_SQL.read_text().split(";"):
                if stmt.strip():
                    conn.execute(text(stmt.strip()))
        conn.commit()
    logger.info("meta service started")
    yield
    logger.info("meta service stopped")


def create_app() -> FastAPI:
    application = FastAPI(
        title="元数据服务",
        description="船舶能效分析平台 - 元数据微服务（燃料类型、船舶类型、时区等）",
        version="0.1.0",
        lifespan=lifespan,
    )

    setup_exception_handlers(application)

    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000)
        logger.info(
            "%s %s %s",
            request.method,
            request.url.path,
            response.status_code,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    application.include_router(router)

    @application.get("/", tags=["健康检查"])
    def health_check() -> ResponseModel:
        return ResponseModel(data={"service": "meta", "version": "0.1.0"}, message="ok")

    return application


app = create_app()
