"""Unified exception hierarchy and FastAPI exception handlers."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


# --- Exception Classes ---


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)


class EntityNotFoundError(AppError):
    """Raised when a database entity is not found."""

    def __init__(self, entity_name: str, entity_id: int | str):
        super().__init__(f"{entity_name} {entity_id} 不存在", code=404)


class ValidationError(AppError):
    """Raised when business validation fails."""

    def __init__(self, message: str):
        super().__init__(message, code=422)


class AuthenticationError(AppError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "认证失败"):
        super().__init__(message, code=401)


class AuthorizationError(AppError):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message, code=403)


# --- Exception Handlers ---


def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on a FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        logger.error("AppError: %s", exc.message)
        return JSONResponse(
            status_code=exc.code,
            content={"code": exc.code, "data": None, "message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.error("Validation error: %s", exc.errors())
        return JSONResponse(
            status_code=422,
            content={"code": 422, "data": exc.errors(), "message": "请求参数不符合要求"},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
        logger.error("Integrity error: %s", exc)
        return JSONResponse(
            status_code=400,
            content={
                "code": 400,
                "data": None,
                "message": f"数据重复或不符合约束: {exc.orig}",
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "data": None, "message": exc.detail},
        )
