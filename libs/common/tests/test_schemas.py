"""Tests for shared Pydantic schemas."""

from common.schemas import ResponseModel


class TestResponseModel:
    def test_default_values(self):
        resp = ResponseModel(data={"key": "value"})
        assert resp.code == 200
        assert resp.message == "success"
        assert resp.data == {"key": "value"}

    def test_custom_values(self):
        resp = ResponseModel(code=201, data="created", message="资源已创建")
        assert resp.code == 201
        assert resp.data == "created"
        assert resp.message == "资源已创建"

    def test_serialization(self):
        resp = ResponseModel(data=[1, 2, 3])
        d = resp.model_dump()
        assert d == {"code": 200, "data": [1, 2, 3], "message": "success"}

    def test_generic_with_list(self):
        resp = ResponseModel[list[str]](data=["a", "b"])
        assert resp.data == ["a", "b"]

    def test_generic_with_none(self):
        resp = ResponseModel(code=404, data=None, message="not found")
        assert resp.data is None
