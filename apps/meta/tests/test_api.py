"""API tests for all meta service endpoints."""


class TestHealthCheck:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["service"] == "meta"


class TestFuelType:
    def test_get_fuel_types(self, client):
        resp = client.get("/meta/fuel_type")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert len(body["data"]) == 2
        assert body["data"][0]["name_abbr"] == "LNG"
        assert body["data"][0]["cf"] == 2.75

    def test_fuel_type_fields(self, client):
        resp = client.get("/meta/fuel_type")
        item = resp.json()["data"][0]
        assert set(item.keys()) == {"id", "name_cn", "name_en", "name_abbr", "cf"}


class TestShipType:
    def test_get_ship_types(self, client):
        resp = client.get("/meta/ship_type")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 2
        assert body["data"][0]["code"] == "I1004"

    def test_ship_type_fields(self, client):
        resp = client.get("/meta/ship_type")
        item = resp.json()["data"][0]
        assert set(item.keys()) == {"id", "name_cn", "name_en", "code", "cii_related_tone"}


class TestTimeZone:
    def test_get_time_zones(self, client):
        resp = client.get("/meta/time_zone")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 2
        assert body["data"][0]["explaination"] == "UTC+8"

    def test_time_zone_fields(self, client):
        resp = client.get("/meta/time_zone")
        item = resp.json()["data"][0]
        assert set(item.keys()) == {"id", "name_cn", "name_en", "explaination"}


class TestAttributes:
    def test_get_attributes(self, client):
        resp = client.get("/meta/attributes")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 11
        attrs = [a["attribute"] for a in body["data"]]
        assert "speed_ground" in attrs
        assert "me_shaft_power" in attrs

    def test_attribute_fields(self, client):
        resp = client.get("/meta/attributes")
        item = resp.json()["data"][0]
        assert set(item.keys()) == {"attribute", "description"}


class TestAttributeMapping:
    def test_get_attribute_mapping(self, client):
        resp = client.get("/meta/attribute_mapping")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 5

    def test_mapping_structure(self, client):
        resp = client.get("/meta/attribute_mapping")
        item = resp.json()["data"][0]
        assert "attribute_left" in item
        assert "attribute_right" in item
        assert "attribute" in item["attribute_left"]
        assert "description" in item["attribute_left"]


class TestFuelTypeCategory:
    def test_get_fuel_type_categories(self, client):
        resp = client.get("/meta/fuel_type_category")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 12

    def test_category_values(self, client):
        resp = client.get("/meta/fuel_type_category")
        values = [c["value"] for c in resp.json()["data"]]
        assert "hfo" in values
        assert "lng" in values
        assert "hydrogen" in values

    def test_category_fields(self, client):
        resp = client.get("/meta/fuel_type_category")
        item = resp.json()["data"][0]
        assert set(item.keys()) == {"label", "value"}
