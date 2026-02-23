"""API tests for the vessel service."""


class TestHealthCheck:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["data"]["service"] == "vessel"


class TestGetVessels:
    def test_list_all(self, client):
        resp = client.get("/vessel")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "测试船舶"

    def test_vessel_nested_fields(self, client):
        resp = client.get("/vessel")
        vessel = resp.json()["data"][0]
        assert "equipments" in vessel
        assert "curves" in vessel
        assert len(vessel["equipments"]) == 2
        assert len(vessel["curves"]) == 1

    def test_equipment_fuel_ids(self, client):
        resp = client.get("/vessel")
        equipments = resp.json()["data"][0]["equipments"]
        me = next(e for e in equipments if e["type"] == "me")
        assert set(me["fuel_type_ids"]) == {1, 2}

    def test_curve_data_points(self, client):
        resp = client.get("/vessel")
        curve = resp.json()["data"][0]["curves"][0]
        assert len(curve["curve_data"]) == 3
        speeds = [cd["speed_water"] for cd in curve["curve_data"]]
        assert speeds == sorted(speeds)  # ordered by speed_water

    def test_filter_by_name(self, client):
        resp = client.get("/vessel", params={"name": "测试"})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_filter_by_name_no_match(self, client):
        resp = client.get("/vessel", params={"name": "不存在"})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 0

    def test_filter_by_company(self, client):
        resp = client.get("/vessel", params={"company_id": 1})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_filter_by_company_no_match(self, client):
        resp = client.get("/vessel", params={"company_id": 999})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 0

    def test_pagination(self, client):
        resp = client.get("/vessel", params={"offset": 1, "limit": 10})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 0


class TestCreateVessel:
    def test_create_basic(self, client):
        payload = {
            "name": "新船舶",
            "mmsi": "987654321",
            "ship_type": 2,
            "build_date": "2022-06-01",
            "gross_tone": 8000.0,
            "dead_weight": 5000.0,
            "company_id": 1,
        }
        resp = client.post("/vessel", json=payload)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "新船舶"
        assert data["mmsi"] == "987654321"
        assert data["equipments"] == []
        assert data["curves"] == []

    def test_create_with_equipment_and_curve(self, client):
        payload = {
            "name": "全配置船",
            "mmsi": "111222333",
            "ship_type": 1,
            "build_date": "2021-03-15",
            "gross_tone": 6000.0,
            "dead_weight": 4000.0,
            "company_id": 2,
            "equipments": [
                {"name": "主机", "type": "me", "fuel_type_ids": [1, 3]},
                {"name": "锅炉", "type": "blr", "fuel_type_ids": [1]},
            ],
            "curves": [
                {
                    "curve_name": "满载",
                    "draft_astern": 10.0,
                    "draft_bow": 10.0,
                    "curve_data": [
                        {"speed_water": 10.0, "me_power": 4000.0},
                        {"speed_water": 13.0, "me_power": 9000.0},
                    ],
                }
            ],
        }
        resp = client.post("/vessel", json=payload)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["equipments"]) == 2
        assert len(data["curves"]) == 1
        assert len(data["curves"][0]["curve_data"]) == 2


class TestGetVessel:
    def test_get_by_id(self, client):
        resp = client.get("/vessel/1")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == 1
        assert data["mmsi"] == "123456789"

    def test_not_found(self, client):
        resp = client.get("/vessel/999")
        assert resp.status_code == 404


class TestUpdateVessel:
    def test_update_name(self, client):
        resp = client.put("/vessel/1", json={"name": "更新船名"})
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "更新船名"

    def test_update_replaces_equipment(self, client):
        new_payload = {
            "equipments": [
                {"name": "新主机", "type": "me", "fuel_type_ids": [2]},
            ],
        }
        resp = client.put("/vessel/1", json=new_payload)
        assert resp.status_code == 200
        equipments = resp.json()["data"]["equipments"]
        assert len(equipments) == 1
        assert equipments[0]["name"] == "新主机"

    def test_update_not_found(self, client):
        resp = client.put("/vessel/999", json={"name": "不存在"})
        assert resp.status_code == 404


class TestDeleteVessel:
    def test_delete(self, client):
        resp = client.delete("/vessel/1")
        assert resp.status_code == 200
        # Verify it's gone
        resp = client.get("/vessel/1")
        assert resp.status_code == 404

    def test_delete_not_found(self, client):
        resp = client.delete("/vessel/999")
        assert resp.status_code == 404
