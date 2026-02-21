"""Tests for exception classes and FastAPI exception handlers."""

import pytest
from common.exceptions import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    EntityNotFoundError,
    ValidationError,
    setup_exception_handlers,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestExceptionClasses:
    def test_app_error(self):
        err = AppError("something wrong", code=500)
        assert err.message == "something wrong"
        assert err.code == 500

    def test_entity_not_found(self):
        err = EntityNotFoundError("User", 42)
        assert err.code == 404
        assert "User" in err.message
        assert "42" in err.message

    def test_validation_error(self):
        err = ValidationError("invalid input")
        assert err.code == 422

    def test_authentication_error(self):
        err = AuthenticationError()
        assert err.code == 401

    def test_authorization_error(self):
        err = AuthorizationError()
        assert err.code == 403


class TestExceptionHandlers:
    @pytest.fixture
    def client(self):
        app = FastAPI()
        setup_exception_handlers(app)

        @app.get("/app-error")
        async def raise_app_error():
            raise AppError("test error", code=400)

        @app.get("/not-found")
        async def raise_not_found():
            raise EntityNotFoundError("Item", 1)

        @app.get("/auth-error")
        async def raise_auth_error():
            raise AuthenticationError()

        return TestClient(app, raise_server_exceptions=False)

    def test_app_error_handler(self, client):
        resp = client.get("/app-error")
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == 400
        assert body["data"] is None
        assert "test error" in body["message"]

    def test_not_found_handler(self, client):
        resp = client.get("/not-found")
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == 404

    def test_auth_error_handler(self, client):
        resp = client.get("/auth-error")
        assert resp.status_code == 401
