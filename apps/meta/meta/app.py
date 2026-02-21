"""FastAPI application entry point for the meta service."""

from contextlib import asynccontextmanager

from common.exceptions import setup_exception_handlers
from common.models import Base
from common.schemas import ResponseModel
from fastapi import FastAPI

from meta.database import engine
from meta.router import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="元数据服务",
        description="船舶能效分析平台 - 元数据微服务（燃料类型、船舶类型、时区等）",
        version="0.1.0",
        lifespan=lifespan,
    )

    setup_exception_handlers(application)
    application.include_router(router)

    @application.get("/", tags=["健康检查"])
    def health_check() -> ResponseModel:
        return ResponseModel(data={"service": "meta", "version": "0.1.0"}, message="ok")

    return application


app = create_app()
