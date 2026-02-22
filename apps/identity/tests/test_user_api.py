"""API tests for user endpoints."""


class TestGetUsers:
    def test_list_all(self, client):
        resp = client.get("/user")
        assert resp.status_code == 200
        body = resp.json()
        # disabled users are excluded
        assert len(body["data"]) == 2

    def test_filter_by_name(self, client):
        resp = client.get("/user", params={"name": "admin"})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
        assert resp.json()["data"][0]["username"] == "admin"

    def test_filter_by_company(self, client):
        resp = client.get("/user", params={"company_id": 1})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_pagination(self, client):
        resp = client.get("/user", params={"offset": 0, "limit": 1})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_user_fields(self, client):
        resp = client.get("/user")
        item = resp.json()["data"][0]
        assert "hashed_password" not in item
        assert set(item.keys()) == {
            "id",
            "username",
            "phone",
            "company_id",
            "is_admin",
            "is_system_admin",
            "disabled",
        }


class TestRegister:
    def test_register(self, client):
        resp = client.post(
            "/user/register",
            json={
                "username": "newuser",
                "password": "pass123",
                "phone": "13600000001",
                "company_id": 1,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["username"] == "newuser"
        assert body["data"]["disabled"] is False
        assert "hashed_password" not in body["data"]


class TestLogin:
    def test_login_success(self, client):
        resp = client.post(
            "/user/login",
            json={
                "username": "admin",
                "password": "admin123",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["username"] == "admin"
        assert "token" in body["data"]
        assert len(body["data"]["token"]) > 0

    def test_login_wrong_password(self, client):
        resp = client.post(
            "/user/login",
            json={
                "username": "admin",
                "password": "wrong",
            },
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/user/login",
            json={
                "username": "nobody",
                "password": "pass",
            },
        )
        assert resp.status_code == 401


class TestGetUser:
    def test_get_by_id(self, client):
        resp = client.get("/user/1")
        assert resp.status_code == 200
        assert resp.json()["data"]["username"] == "admin"

    def test_disabled_user_not_found(self, client):
        resp = client.get("/user/3")
        assert resp.status_code == 404

    def test_nonexistent_user(self, client):
        resp = client.get("/user/999")
        assert resp.status_code == 404


class TestUpdateUser:
    def test_update_phone(self, client):
        resp = client.put("/user/1", json={"phone": "13999999999"})
        assert resp.status_code == 200
        assert resp.json()["data"]["phone"] == "13999999999"


class TestDeleteUser:
    def test_soft_delete(self, client):
        resp = client.delete("/user/2")
        assert resp.status_code == 200
        assert resp.json()["data"]["disabled"] is True

        # Now user should not be accessible
        resp = client.get("/user/2")
        assert resp.status_code == 404
