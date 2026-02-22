"""API tests for company endpoints."""


class TestHealthCheck:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["data"]["service"] == "identity"


class TestGetCompanies:
    def test_list_all(self, client):
        resp = client.get("/company")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 2

    def test_company_fields(self, client):
        resp = client.get("/company")
        item = resp.json()["data"][0]
        assert set(item.keys()) == {
            "id",
            "name",
            "address",
            "contact_person",
            "contact_phone",
            "contact_email",
        }


class TestCreateCompany:
    def test_create(self, client):
        resp = client.post(
            "/company",
            json={
                "name": "新公司",
                "address": "深圳市南山区",
                "contact_person": "王五",
                "contact_phone": "13700000001",
                "contact_email": "new@test.com",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["name"] == "新公司"
        assert body["data"]["id"] is not None


class TestGetCompany:
    def test_get_by_id(self, client):
        resp = client.get("/company/1")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "测试公司A"

    def test_not_found(self, client):
        resp = client.get("/company/999")
        assert resp.status_code == 404


class TestUpdateCompany:
    def test_update(self, client):
        resp = client.put("/company/1", json={"name": "更新公司A"})
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "更新公司A"

    def test_partial_update(self, client):
        resp = client.put("/company/1", json={"address": "新地址"})
        assert resp.status_code == 200
        assert resp.json()["data"]["address"] == "新地址"
        assert resp.json()["data"]["name"] == "测试公司A"


class TestDeleteCompany:
    def test_delete(self, client):
        resp = client.delete("/company/2")
        assert resp.status_code == 200

        resp = client.get("/company/2")
        assert resp.status_code == 404
