"""FastAPI application entry point for the vessel service."""

import logging
import time
from contextlib import asynccontextmanager

from common.exceptions import setup_exception_handlers
from common.logging import setup_logging
from common.models import Base
from common.schemas import ResponseModel
from fastapi import FastAPI, Request

from vessel.config import settings
from vessel.database import engine
from vessel.router import vessel_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging("vessel", settings.log_level)
    Base.metadata.create_all(bind=engine)
    logger.info("vessel service started")
    yield
    logger.info("vessel service stopped")


def create_app() -> FastAPI:
    application = FastAPI(
        title="船舶管理服务",
        description="船舶能效分析平台 - 船舶信息与设备管理微服务",
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

    application.include_router(vessel_router)

    @application.get("/", tags=["健康检查"])
    def health_check() -> ResponseModel:
        return ResponseModel(data={"service": "vessel", "version": "0.1.0"}, message="ok")

    return application


app = create_app()
