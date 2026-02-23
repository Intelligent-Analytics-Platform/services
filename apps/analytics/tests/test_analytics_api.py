"""Tests for the analytics service API."""

from __future__ import annotations

from unittest.mock import patch

from analytics.cii_rating import (
    get_cii_boundaries,
    get_cii_rating,
    get_required_cii,
)

# ── Health check ─────────────────────────────────────────────────────────────


def test_health_check(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["service"] == "analytics"


# ── CII rating (pure functions, no DB needed) ─────────────────────────────────


class TestCiiRating:
    def test_get_required_cii_basic(self):
        # I001, dwt=279000, year=2023
        req = get_required_cii(2023, "I001", 279000, 0)
        assert req > 0

    def test_get_cii_rating_returns_valid_grade(self):
        req = get_required_cii(2023, "I001", 279000, 0)
        for cii_val, expected_grade in [
            (req * 0.5, "A"),  # well below superior → A
            (req * 2.0, "E"),  # well above inferior → E
        ]:
            rating = get_cii_rating(cii_val, 2023, "I001", 279000, 0)
            assert rating in ("A", "B", "C", "D", "E", "N/A")
            assert rating == expected_grade

    def test_get_cii_boundaries_keys(self):
        bounds = get_cii_boundaries(2023, "I001", 279000, 0)
        assert set(bounds.keys()) == {"superior", "lower", "upper", "inferior"}
        assert bounds["superior"] < bounds["lower"] < bounds["upper"] < bounds["inferior"]

    def test_unknown_ship_type_returns_na(self):
        rating = get_cii_rating(10.0, 2023, "UNKNOWN", 50000, 0)
        assert rating == "N/A"


# ── Statistic endpoints ───────────────────────────────────────────────────────


class TestStatisticEndpoints:
    def test_attribute_frequencies(self, client):
        resp = client.get(
            "/statistic/attribute-frequencies",
            params={
                "attribute_name": "speed_water",
                "vessel_id": 1,
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
                "min_slip_ratio": -20,
                "max_slip_ratio": 20,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body

    def test_attribute_frequencies_invalid_column(self, client):
        resp = client.get(
            "/statistic/attribute-frequencies",
            params={
                "attribute_name": "DROP TABLE vessel_data_per_day",
                "vessel_id": 1,
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
                "min_slip_ratio": -20,
                "max_slip_ratio": 20,
            },
        )
        assert resp.status_code == 400

    def test_attribute_values(self, client):
        resp = client.get(
            "/statistic/attribute-values",
            params={
                "attribute_name": "speed_water",
                "vessel_id": 1,
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
                "min_slip_ratio": -20,
                "max_slip_ratio": 20,
            },
        )
        assert resp.status_code == 200

    def test_attribute_relation(self, client):
        resp = client.get(
            "/statistic/attribute-relation",
            params={
                "attribute_name1": "speed_water",
                "attribute_name2": "me_shaft_power",
                "vessel_id": 1,
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
                "min_slip_ratio": -20,
                "max_slip_ratio": 20,
            },
        )
        assert resp.status_code == 200

    def test_vessel_completeness(self, client):
        resp = client.get("/statistic/vessel/1/completeness")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["data"], list)

    def test_vessel_date_range(self, client):
        resp = client.get(
            "/statistic/vessel/1/date-range",
            params={
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
                "sample_interval": 1,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 2  # we seeded 2 rows

    def test_consumption_nmile(self, client):
        resp = client.get(
            "/statistic/consumption/nmile",
            params={
                "fuel_type": "hfo",
                "vessel_id": 1,
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "total" in body["data"]

    def test_consumption_total(self, client):
        resp = client.get(
            "/statistic/consumption/total",
            params={
                "fuel_type": "hfo",
                "vessel_id": 1,
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "me" in body["data"]
        assert body["data"]["me"] > 0  # we seeded 20.0

    def test_consumption_invalid_fuel_type(self, client):
        resp = client.get(
            "/statistic/consumption/total",
            params={
                "fuel_type": "diesel_DROP",
                "vessel_id": 1,
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
            },
        )
        assert resp.status_code == 400


# ── Optimisation endpoints ────────────────────────────────────────────────────


class TestOptimizationEndpoints:
    _MOCK_VESSEL = {
        "id": 1,
        "ship_type": 4,
        "dead_weight": 35337.0,
        "gross_tone": 26771.0,
        "pitch": 6.058,
    }
    _MOCK_SHIP_TYPES = [{"id": 4, "code": "I004"}]

    def test_vessel_average(self, client):
        resp = client.get(
            "/optimization/vessel/1/average",
            params={"start_date": "2023-01-01", "end_date": "2023-01-31"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "speed_water" in body["data"]

    def test_optimization_values_no_vessel_service(self, client):
        """Without vessel service, endpoint returns 5xx."""
        resp = client.get(
            "/optimization/vessel/999/values",
            params={"start_date": "2023-01-01", "end_date": "2023-01-31"},
        )
        # vessel 999 doesn't exist; vessel service is unavailable → 502/503
        assert resp.status_code in (404, 502, 503)

    def test_trim_data(self, client):
        with (
            patch("analytics.client.get_vessel", return_value=self._MOCK_VESSEL),
            patch("analytics.client.get_ship_type_map", return_value={4: "I004"}),
        ):
            resp = client.get(
                "/optimization/trim-data/1",
                params={"start_date": "2023-01-01", "end_date": "2023-01-31"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "trim_values" in body["data"]
        assert "averages" in body["data"]

    def test_optimize_speed_no_model(self, client):
        with (
            patch("analytics.client.get_vessel", return_value=self._MOCK_VESSEL),
            patch("analytics.client.get_ship_type_map", return_value={4: "I004"}),
            patch("analytics.config.settings.models_dir", "/nonexistent"),
        ):
            resp = client.get(
                "/optimization/optimize-speed/1",
                params={"start_date": "2023-01-01", "end_date": "2023-01-31"},
            )
        assert resp.status_code == 404  # no model found
