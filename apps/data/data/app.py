"""FastAPI application entry point for the data service."""

import logging
import time
from contextlib import asynccontextmanager

from common.exceptions import setup_exception_handlers
from common.logging import setup_logging
from common.models import Base
from common.schemas import ResponseModel
from fastapi import FastAPI, Request

from data.config import settings
from data.database import engine, init_duck_db
from data.router import data_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging("data", settings.log_level)
    # SQLite: create upload records table
    Base.metadata.create_all(bind=engine)
    # DuckDB: create analytics tables
    init_duck_db()
    logger.info("data service started")
    yield
    logger.info("data service stopped")


def create_app() -> FastAPI:
    application = FastAPI(
        title="数据服务",
        description="船舶能效分析平台 - 遥测数据上传、清洗、存储与 CII 计算",
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

    application.include_router(data_router)

    @application.get("/", tags=["健康检查"])
    def health_check() -> ResponseModel:
        return ResponseModel(data={"service": "data", "version": "0.1.0"}, message="ok")

    return application


app = create_app()
