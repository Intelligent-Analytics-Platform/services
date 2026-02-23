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
        assert len(body["data"]) == 16
        abbrs = [t["name_abbr"] for t in body["data"]]
        assert "HFO-HS" in abbrs
        assert "LNG" in abbrs
        assert "Hydrogen" in abbrs

    def test_fuel_type_fields(self, client):
        resp = client.get("/meta/fuel_type")
        item = resp.json()["data"][0]
        assert set(item.keys()) == {"id", "name_cn", "name_en", "name_abbr", "cf"}

    def test_fuel_type_cf_values(self, client):
        resp = client.get("/meta/fuel_type")
        by_abbr = {t["name_abbr"]: t for t in resp.json()["data"]}
        assert by_abbr["LNG"]["cf"] == 2.75
        assert by_abbr["Methanol"]["cf"] == 1.375
        assert by_abbr["Ammonia"]["cf"] == 0.0


class TestShipType:
    def test_get_ship_types(self, client):
        resp = client.get("/meta/ship_type")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 13
        codes = [t["code"] for t in body["data"]]
        assert "I001" in codes
        assert "I004" in codes
        assert "I012" in codes

    def test_ship_type_fields(self, client):
        resp = client.get("/meta/ship_type")
        item = resp.json()["data"][0]
        assert set(item.keys()) == {"id", "name_cn", "name_en", "code", "cii_related_tone"}

    def test_ship_type_cii_tones(self, client):
        resp = client.get("/meta/ship_type")
        by_code = {t["code"]: t for t in resp.json()["data"]}
        assert by_code["I001"]["cii_related_tone"] == "dwt"  # Bulk carrier
        assert by_code["I009"]["cii_related_tone"] == "gt"   # Ro-ro (vehicle carrier)


class TestTimeZone:
    def test_get_time_zones(self, client):
        resp = client.get("/meta/time_zone")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 25
        names = [t["name_en"] for t in body["data"]]
        assert "UTC+0" in names
        assert "UTC+8" in names
        assert "UTC-12" in names

    def test_time_zone_fields(self, client):
        resp = client.get("/meta/time_zone")
        item = resp.json()["data"][0]
        assert set(item.keys()) == {"id", "name_cn", "name_en", "explaination"}

    def test_time_zone_explaination(self, client):
        resp = client.get("/meta/time_zone")
        by_name = {t["name_en"]: t for t in resp.json()["data"]}
        assert "120° E" in by_name["UTC+8"]["explaination"]


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

    def test_attribute_descriptions_are_chinese(self, client):
        resp = client.get("/meta/attributes")
        by_attr = {a["attribute"]: a for a in resp.json()["data"]}
        assert by_attr["speed_water"]["description"] == "对水航速"
        assert by_attr["me_shaft_power"]["description"] == "主机功率"


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

    def test_mapping_pairs_are_valid(self, client):
        resp = client.get("/meta/attribute_mapping")
        lefts = [m["attribute_left"]["attribute"] for m in resp.json()["data"]]
        assert "speed_water" in lefts
        assert "me_rpm" in lefts
        assert "me_shaft_power" in lefts


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
