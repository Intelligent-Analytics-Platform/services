"""FastAPI application entry point for the analytics service."""

import logging
import time
from contextlib import asynccontextmanager

from common.exceptions import setup_exception_handlers
from common.logging import setup_logging
from common.schemas import ResponseModel
from fastapi import FastAPI, Request

from analytics.config import settings
from analytics.router import analytics_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging("analytics", settings.log_level)
    logger.info("analytics service started (DuckDB: %s)", settings.duck_db_path)
    yield
    logger.info("analytics service stopped")


def create_app() -> FastAPI:
    application = FastAPI(
        title="数据分析服务",
        description=(
            "船舶能效分析平台 - 统计分析（直方图/散点图/CII/能耗）与优化建议（航速/吃水差）。\n\n"
            "**数据来源**：只读访问 data 服务的 DuckDB 文件"
            "（vessel_standard_data / vessel_data_per_day）。\n"
            "**CII评级**：调用 vessel 服务与 meta 服务获取船型参数。\n"
            "**ML优化**：需在 `MODELS_DIR` 目录中放置对应 XGBoost pkl 模型文件。"
        ),
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

    application.include_router(analytics_router)

    @application.get("/", tags=["健康检查"])
    def health_check() -> ResponseModel:
        return ResponseModel(data={"service": "analytics", "version": "0.1.0"}, message="ok")

    return application


app = create_app()
