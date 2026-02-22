"""FastAPI application entry point for the identity service."""

from contextlib import asynccontextmanager

from common.exceptions import setup_exception_handlers
from common.models import Base
from common.schemas import ResponseModel
from fastapi import FastAPI

from identity.database import engine
from identity.router import company_router, user_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="身份认证服务",
        description="船舶能效分析平台 - 公司管理与用户认证微服务",
        version="0.1.0",
        lifespan=lifespan,
    )

    setup_exception_handlers(application)
    application.include_router(company_router)
    application.include_router(user_router)

    @application.get("/", tags=["健康检查"])
    def health_check() -> ResponseModel:
        return ResponseModel(data={"service": "identity", "version": "0.1.0"}, message="ok")

    return application


app = create_app()
