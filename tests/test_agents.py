"""Unit tests for all 4 worker fraud detection agents."""
import pytest
import numpy as np


# ---------------------------------------------------------------------------
# Velocity Agent fixtures & tests
# ---------------------------------------------------------------------------

@pytest.fixture
def velocity_profiles():
    """Card profiles for velocity agent testing."""
    return {
        "card_normal": {
            "amounts": [50, 45, 55, 60, 48, 52],
            "timestamps": [1000, 2000, 3000, 4000, 5000, 6000],
            "merchants": ["m1", "m1", "m2", "m1", "m2", "m1"],
            "categories": ["W", "W", "W", "H", "W", "W"],
            "fraud_count": 0,
            "last_addr1": 200.0,
            "last_device_type": "desktop",
        },
        "card_burst": {
            "amounts": [30, 35, 25, 40, 33, 28],
            "timestamps": [10000, 10050, 10100, 10150, 10200, 10250],
            "merchants": ["m1", "m2", "m3", "m4", "m5", "m6"],
            "categories": ["W", "W", "W", "W", "W", "W"],
            "fraud_count": 0,
            "last_addr1": 150.0,
            "last_device_type": "desktop",
        },
        "card_night": {
            "amounts": [100, 110, 95, 105, 120, 90, 100, 115, 108, 102],
            # All timestamps map to ~10:00 (36000/3600=10h), stepping 86400s (24h)
            # so (ts/3600)%24 = 10 for all -- 0% night activity
            "timestamps": [36000, 122400, 208800, 295200, 381600,
                           468000, 554400, 640800, 727200, 813600],
            "merchants": ["m1", "m2", "m1", "m1", "m2",
                           "m1", "m2", "m1", "m1", "m2"],
            "categories": ["W", "W", "W", "W", "W",
                           "W", "W", "W", "W", "W"],
            "fraud_count": 0,
            "last_addr1": 200.0,
            "last_device_type": "desktop",
        },
    }


class TestVelocityAgent:
    """Tests for VelocityAgent."""

    def test_velocity_high_amount(self, velocity_profiles):
        """Card with profile (5+ txns, mean ~$50), new txn $500 -> risk_score > 40."""
        from backend.agents.velocity_agent import VelocityAgent
        agent = VelocityAgent(velocity_profiles)
        result = agent.analyze({
            "card_id": "card_normal",
            "amount": 500,
            "timestamp": 7000,
            "hour_of_day": 12,
        })
        assert result.risk_score > 40
        assert any("std dev" in s.lower() or "z-score" in s.lower() or "σ" in s
                    for s in result.signals), f"Expected z-score signal, got: {result.signals}"
        assert result.agent_name == "Velocity Agent"

    def test_velocity_burst(self, velocity_profiles):
        """Card with timestamps close together (3+ in 300s) -> risk_score > 30."""
        from backend.agents.velocity_agent import VelocityAgent
        agent = VelocityAgent(velocity_profiles)
        result = agent.analyze({
            "card_id": "card_burst",
            "amount": 32,
            "timestamp": 10260,
            "hour_of_day": 14,
        })
        assert result.risk_score > 30
        assert any("burst" in s.lower() or "5 minute" in s.lower()
                    for s in result.signals), f"Expected burst signal, got: {result.signals}"

    def test_velocity_night(self, velocity_profiles):
        """Transaction at hour=3 for card with <10% night history -> signals mention night."""
        from backend.agents.velocity_agent import VelocityAgent
        agent = VelocityAgent(velocity_profiles)
        # All profile timestamps map to hour 10 (0% night activity)
        result = agent.analyze({
            "card_id": "card_night",
            "amount": 105,
            "timestamp": 900000,
            "hour_of_day": 3,
        })
        assert any("night" in s.lower() or "unusual" in s.lower() or ":00" in s
                    for s in result.signals), f"Expected night signal, got: {result.signals}"

    def test_velocity_normal(self, velocity_profiles):
        """Card with profile, amount near mean, daytime -> risk_score < 20."""
        from backend.agents.velocity_agent import VelocityAgent
        agent = VelocityAgent(velocity_profiles)
        result = agent.analyze({
            "card_id": "card_normal",
            "amount": 52,
            "timestamp": 50000,
            "hour_of_day": 14,
        })
        assert result.risk_score < 20

    def test_velocity_unknown_card(self, velocity_profiles):
        """Card not in profiles -> low default score."""
        from backend.agents.velocity_agent import VelocityAgent
        agent = VelocityAgent(velocity_profiles)
        result = agent.analyze({
            "card_id": "card_UNKNOWN",
            "amount": 50,
            "timestamp": 1000,
            "hour_of_day": 12,
        })
        assert result.risk_score < 36
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0


# ---------------------------------------------------------------------------
# Geolocation Agent fixtures & tests
# ---------------------------------------------------------------------------

@pytest.fixture
def geo_profiles():
    """Card profiles for geolocation agent testing."""
    return {
        "card_travel": {
            "amounts": [100, 200],
            "timestamps": [10000, 10500],
            "merchants": ["m1", "m2"],
            "categories": ["W", "W"],
            "fraud_count": 0,
            "last_addr1": 100.0,
            "last_device_type": "desktop",
        },
        "card_stable": {
            "amounts": [50, 60, 55],
            "timestamps": [1000, 2000, 3000],
            "merchants": ["m1", "m1", "m1"],
            "categories": ["W", "W", "W"],
            "fraud_count": 0,
            "last_addr1": 200.0,
            "last_device_type": "desktop",
        },
    }


class TestGeolocationAgent:
    """Tests for GeolocationAgent."""

    def test_geo_impossible_travel(self, geo_profiles):
        """Last addr1=100, new addr1=450, time_diff < 1 hour -> risk_score > 50."""
        from backend.agents.geolocation_agent import GeolocationAgent
        agent = GeolocationAgent(geo_profiles)
        result = agent.analyze({
            "card_id": "card_travel",
            "addr1": 450,
            "addr2": 50,
            "device_type": "desktop",
            "timestamp": 11000,
            "hour_of_day": 12,
        })
        assert result.risk_score > 50
        assert any("impossible" in s.lower() or "rapid" in s.lower() or "travel" in s.lower()
                    for s in result.signals), f"Expected travel signal, got: {result.signals}"

    def test_geo_address_mismatch(self, geo_profiles):
        """addr1 and addr2 differ by >200 -> signals mention address discrepancy."""
        from backend.agents.geolocation_agent import GeolocationAgent
        agent = GeolocationAgent(geo_profiles)
        result = agent.analyze({
            "card_id": "card_stable",
            "addr1": 201,
            "addr2": 1,
            "device_type": "desktop",
            "timestamp": 50000,
            "hour_of_day": 12,
        })
        # Note: 201 - 1 = 200, we need > 200 so test with wider gap
        result2 = agent.analyze({
            "card_id": "card_stable",
            "addr1": 400,
            "addr2": 50,
            "device_type": "desktop",
            "timestamp": 60000,
            "hour_of_day": 12,
        })
        assert any("address" in s.lower() or "discrepancy" in s.lower()
                    for s in result2.signals), f"Expected address signal, got: {result2.signals}"

    def test_geo_device_change(self, geo_profiles):
        """Profile has desktop, new txn mobile -> signals mention device change."""
        from backend.agents.geolocation_agent import GeolocationAgent
        agent = GeolocationAgent(geo_profiles)
        result = agent.analyze({
            "card_id": "card_stable",
            "addr1": 200,
            "addr2": 50,
            "device_type": "mobile",
            "timestamp": 50000,
            "hour_of_day": 12,
        })
        assert any("device" in s.lower() for s in result.signals), \
            f"Expected device change signal, got: {result.signals}"

    def test_geo_normal(self, geo_profiles):
        """Same address region, same device -> risk_score < 15."""
        from backend.agents.geolocation_agent import GeolocationAgent
        agent = GeolocationAgent(geo_profiles)
        result = agent.analyze({
            "card_id": "card_stable",
            "addr1": 201,
            "addr2": 55,
            "device_type": "desktop",
            "timestamp": 50000,
            "hour_of_day": 12,
        })
        assert result.risk_score < 15

    def test_geo_unknown_card(self, geo_profiles):
        """Card not in profiles -> low default score."""
        from backend.agents.geolocation_agent import GeolocationAgent
        agent = GeolocationAgent(geo_profiles)
        result = agent.analyze({
            "card_id": "card_UNKNOWN",
            "addr1": 200,
            "addr2": 50,
            "device_type": "desktop",
            "timestamp": 1000,
            "hour_of_day": 12,
        })
        assert result.risk_score < 15
        assert result.agent_name == "Geolocation Agent"
        assert isinstance(result.signals, list)
        assert isinstance(result.explanation, str)
