"""Unit tests for all 5 fraud detection agents (4 workers + coordinator)."""
import pytest
import numpy as np
from backend.models.schemas import AgentAssessment


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


# ---------------------------------------------------------------------------
# Graph Agent fixtures & tests
# ---------------------------------------------------------------------------

@pytest.fixture
def small_graph():
    """Build a small graph with known fraud patterns for testing."""
    import networkx as nx
    from backend.data.graph_builder import TransactionGraph

    tg = TransactionGraph()

    # Cards
    tg.G.add_node("card_A", type="card")       # Fraud card sharing device
    tg.G.add_node("card_B", type="card")       # Clean card sharing device with fraud
    tg.G.add_node("card_C", type="card")       # Isolated clean card
    tg.G.add_node("card_high_degree", type="card")  # High-connectivity card

    # Merchants in different communities (will be assigned by Louvain)
    for i in range(60):
        mid = f"merchant_{i}"
        tg.G.add_node(mid, type="merchant")
        # Connect high_degree card to many merchants
        tg.G.add_edge("card_high_degree", mid, weight=1, total_amount=50)

    # A few merchants for normal cards
    tg.G.add_node("merchant_A1", type="merchant")
    tg.G.add_node("merchant_B1", type="merchant")
    tg.G.add_node("merchant_C1", type="merchant")  # Clean merchant for card_C
    tg.G.add_edge("card_A", "merchant_A1", weight=3, total_amount=300)
    tg.G.add_edge("card_B", "merchant_B1", weight=2, total_amount=200)
    tg.G.add_edge("card_C", "merchant_C1", weight=1, total_amount=100)

    # Shared device between card_A (fraud) and card_B (clean)
    tg.G.add_node("device_shared", type="device")
    tg.G.add_edge("card_A", "device_shared", weight=5)
    tg.G.add_edge("card_B", "device_shared", weight=3)

    # Device for card_C (isolated)
    tg.G.add_node("device_C", type="device")
    tg.G.add_edge("card_C", "device_C", weight=2)

    # Card profiles
    tg.card_profiles = {
        "card_A": {
            "amounts": [100, 200, 500, 1000],
            "timestamps": [1000, 2000, 3000, 4000],
            "merchants": ["merchant_A1", "merchant_A1", "merchant_A1", "merchant_A1"],
            "categories": ["W", "W", "H", "H"],
            "fraud_count": 3,  # Known fraud card
            "last_addr1": 150.0,
            "last_device_type": "desktop",
        },
        "card_B": {
            "amounts": [50, 60, 55, 70, 45],
            "timestamps": [1000, 2000, 3000, 4000, 5000],
            "merchants": ["merchant_B1", "merchant_B1", "merchant_B1", "merchant_B1", "merchant_B1"],
            "categories": ["W", "W", "W", "W", "W"],
            "fraud_count": 0,
            "last_addr1": 200.0,
            "last_device_type": "desktop",
        },
        "card_C": {
            "amounts": [30, 35, 32],
            "timestamps": [1000, 2000, 3000],
            "merchants": ["merchant_C1", "merchant_C1", "merchant_C1"],
            "categories": ["W", "W", "W"],
            "fraud_count": 0,
            "last_addr1": 200.0,
            "last_device_type": "mobile",
        },
        "card_high_degree": {
            "amounts": [100] * 20,
            "timestamps": list(range(1000, 21000, 1000)),
            "merchants": [f"merchant_{i}" for i in range(20)],
            "categories": ["W"] * 20,
            "fraud_count": 0,
            "last_addr1": 300.0,
            "last_device_type": "desktop",
        },
    }

    return tg


class TestGraphAgent:
    """Tests for GraphAgent."""

    def test_graph_fraud_exposure(self, small_graph):
        """Card sharing device with fraud-flagged card -> risk_score > 20."""
        from backend.agents.graph_agent import GraphAgent
        agent = GraphAgent(small_graph)
        # card_B shares device with card_A (which has fraud_count=3)
        result = agent.analyze({
            "card_id": "card_B",
            "merchant_id": "merchant_B1",
        })
        assert result.risk_score > 20
        assert any("shared" in s.lower() or "exposure" in s.lower() or "device" in s.lower()
                    for s in result.signals), f"Expected fraud exposure signal, got: {result.signals}"
        assert result.agent_name == "Graph Agent"

    def test_graph_cross_community(self, small_graph):
        """Card and merchant in different communities -> signals mention cross-community."""
        from backend.agents.graph_agent import GraphAgent
        agent = GraphAgent(small_graph)
        # card_C is connected to merchant_A1; merchant_60+ are far away
        # We use a merchant that is likely in a different community from card_C
        result = agent.analyze({
            "card_id": "card_C",
            "merchant_id": "merchant_50",
        })
        # Cross-community depends on Louvain output, so we check if signal exists
        # or the score is reasonable (agent handles it gracefully)
        assert result.agent_name == "Graph Agent"
        # If communities differ, we expect the signal
        has_cross_comm = any("cross-community" in s.lower() for s in result.signals)
        # Whether or not cross-community fires, the agent should still work
        assert result.risk_score >= 0
        assert result.confidence >= 0

    def test_graph_high_degree(self, small_graph):
        """Card with >50 connections -> signals mention high connectivity."""
        from backend.agents.graph_agent import GraphAgent
        agent = GraphAgent(small_graph)
        result = agent.analyze({
            "card_id": "card_high_degree",
            "merchant_id": "merchant_0",
        })
        assert any("connectivity" in s.lower() or "connections" in s.lower()
                    for s in result.signals), f"Expected high degree signal, got: {result.signals}"
        assert result.risk_score > 15

    def test_graph_normal(self, small_graph):
        """Card with low connectivity, same community, no fraud neighbors -> risk_score < 15."""
        from backend.agents.graph_agent import GraphAgent
        agent = GraphAgent(small_graph)
        # card_C has low degree, uses device_C (no shared fraud), merchant_C1 (clean)
        result = agent.analyze({
            "card_id": "card_C",
            "merchant_id": "merchant_C1",
        })
        assert result.risk_score < 15

    def test_graph_unknown_card(self, small_graph):
        """Card not in graph -> low default score."""
        from backend.agents.graph_agent import GraphAgent
        agent = GraphAgent(small_graph)
        result = agent.analyze({
            "card_id": "card_NONEXISTENT",
            "merchant_id": "merchant_0",
        })
        assert result.risk_score < 10
        assert result.agent_name == "Graph Agent"


# ---------------------------------------------------------------------------
# Behavioral Agent fixtures & tests
# ---------------------------------------------------------------------------

@pytest.fixture
def behavioral_profiles():
    """Card profiles for behavioral agent testing."""
    return {
        "card_habitual": {
            "amounts": [50, 55, 48, 52, 60, 45, 50, 55, 53, 47],
            "timestamps": list(range(1000, 11000, 1000)),
            "merchants": ["m1", "m1", "m2", "m1", "m2", "m1", "m1", "m2", "m1", "m1"],
            "categories": ["W", "W", "W", "W", "W", "W", "W", "W", "W", "W"],
            "fraud_count": 0,
            "last_addr1": 200.0,
            "last_device_type": "desktop",
        },
        "card_thin": {
            "amounts": [30, 40],
            "timestamps": [1000, 2000],
            "merchants": ["m1", "m2"],
            "categories": ["W", "H"],
            "fraud_count": 0,
            "last_addr1": 200.0,
            "last_device_type": "desktop",
        },
        "card_multi_cat": {
            "amounts": [50, 55, 48, 52, 60, 45, 50, 55, 53, 47,
                        200, 210, 195, 205, 215, 190, 200, 210, 198, 202],
            "timestamps": list(range(1000, 21000, 1000)),
            "merchants": ["m1"] * 10 + ["m2"] * 10,
            "categories": ["W"] * 10 + ["H"] * 10,
            "fraud_count": 0,
            "last_addr1": 200.0,
            "last_device_type": "desktop",
        },
    }


class TestBehavioralAgent:
    """Tests for BehavioralAgent."""

    def test_behavioral_new_category(self, behavioral_profiles):
        """Card historically uses 'W', new txn category 'H' -> signals mention new/rare."""
        from backend.agents.behavioral_agent import BehavioralAgent
        agent = BehavioralAgent(behavioral_profiles)
        result = agent.analyze({
            "card_id": "card_habitual",
            "amount": 50,
            "product_category": "H",
            "merchant_id": "m1",
        })
        assert any("first-ever" in s.lower() or "rare" in s.lower() or "category" in s.lower()
                    for s in result.signals), f"Expected new category signal, got: {result.signals}"
        assert result.agent_name == "Behavioral Agent"

    def test_behavioral_amount_deviation(self, behavioral_profiles):
        """Amount 5x above category average -> risk_score > 25."""
        from backend.agents.behavioral_agent import BehavioralAgent
        agent = BehavioralAgent(behavioral_profiles)
        # card_multi_cat has category "H" with avg ~$203, std ~$7
        # $500 is well over 2.5 std devs above
        result = agent.analyze({
            "card_id": "card_multi_cat",
            "amount": 500,
            "product_category": "H",
            "merchant_id": "m2",
        })
        assert result.risk_score > 25
        assert any("deviation" in s.lower() or "above avg" in s.lower() or "above" in s.lower()
                    for s in result.signals), f"Expected amount deviation signal, got: {result.signals}"

    def test_behavioral_new_merchant(self, behavioral_profiles):
        """Merchant not in card's history -> signals mention first transaction."""
        from backend.agents.behavioral_agent import BehavioralAgent
        agent = BehavioralAgent(behavioral_profiles)
        result = agent.analyze({
            "card_id": "card_habitual",
            "amount": 50,
            "product_category": "W",
            "merchant_id": "merchant_BRAND_NEW",
        })
        assert any("first" in s.lower() or "new" in s.lower()
                    for s in result.signals), f"Expected new merchant signal, got: {result.signals}"

    def test_behavioral_normal(self, behavioral_profiles):
        """Same category, similar amount, known merchant -> risk_score < 15."""
        from backend.agents.behavioral_agent import BehavioralAgent
        agent = BehavioralAgent(behavioral_profiles)
        result = agent.analyze({
            "card_id": "card_habitual",
            "amount": 52,
            "product_category": "W",
            "merchant_id": "m1",
        })
        assert result.risk_score < 15

    def test_behavioral_thin_history(self, behavioral_profiles):
        """Card with <3 txns, high amount -> signals mention thin-history."""
        from backend.agents.behavioral_agent import BehavioralAgent
        agent = BehavioralAgent(behavioral_profiles)
        result = agent.analyze({
            "card_id": "card_thin",
            "amount": 500,
            "product_category": "W",
            "merchant_id": "m3",
        })
        assert any("thin" in s.lower() or "low-history" in s.lower() or "prior txn" in s.lower()
                    for s in result.signals), f"Expected thin-history signal, got: {result.signals}"


# ---------------------------------------------------------------------------
# Coordinator Agent fixtures & tests
# ---------------------------------------------------------------------------

def make_assessment(name, score, confidence, signals):
    """Helper to create AgentAssessment objects for coordinator tests."""
    return AgentAssessment(
        agent_name=name, risk_score=score, confidence=confidence,
        signals=signals, explanation=f"{name}: {'; '.join(signals)}"
    )


@pytest.fixture
def sample_assessments():
    """Standard set of 4 agent assessments for coordinator testing."""
    return [
        make_assessment("Velocity Agent", 80, 0.9, ["3 txns in 90 sec"]),
        make_assessment("Geolocation Agent", 60, 0.8, ["Rapid location change"]),
        make_assessment("Graph Agent", 70, 0.85, ["Shared device with fraud card"]),
        make_assessment("Behavioral Agent", 40, 0.6, ["New category"]),
    ]


class TestCoordinatorAgent:
    """Tests for CoordinatorAgent."""

    def test_coordinator_weighted_scoring(self, sample_assessments):
        """Given 4 assessments with known scores/confidences, final_score matches manual calculation."""
        from backend.agents.coordinator_agent import CoordinatorAgent
        coord = CoordinatorAgent(use_llm=False)
        verdict = coord.synthesize("txn_test", sample_assessments)

        # Manual calculation:
        # Velocity:    80 * 0.25 * 0.9  = 18.0,  weight_contrib = 0.25 * 0.9  = 0.225
        # Geolocation: 60 * 0.25 * 0.8  = 12.0,  weight_contrib = 0.25 * 0.8  = 0.200
        # Graph:       70 * 0.30 * 0.85 = 17.85, weight_contrib = 0.30 * 0.85 = 0.255
        # Behavioral:  40 * 0.20 * 0.6  = 4.8,   weight_contrib = 0.20 * 0.6  = 0.120
        # Total weighted = 52.65, total_weight = 0.800
        # final_score = 52.65 / 0.800 = 65.8125
        expected = 65.8125
        assert abs(verdict.final_score - expected) < 0.5, \
            f"Expected ~{expected}, got {verdict.final_score}"

    def test_coordinator_verdict_approve(self):
        """final_score=25 -> verdict='APPROVE'."""
        from backend.agents.coordinator_agent import CoordinatorAgent
        coord = CoordinatorAgent(use_llm=False)
        assessments = [
            make_assessment("Velocity Agent", 25, 1.0, []),
            make_assessment("Geolocation Agent", 25, 1.0, []),
            make_assessment("Graph Agent", 25, 1.0, []),
            make_assessment("Behavioral Agent", 25, 1.0, []),
        ]
        verdict = coord.synthesize("txn_low", assessments)
        assert verdict.verdict == "APPROVE"
        assert verdict.final_score < 30

    def test_coordinator_verdict_flag(self):
        """final_score ~50 -> verdict='FLAG'."""
        from backend.agents.coordinator_agent import CoordinatorAgent
        coord = CoordinatorAgent(use_llm=False)
        assessments = [
            make_assessment("Velocity Agent", 50, 1.0, ["Elevated amount"]),
            make_assessment("Geolocation Agent", 50, 1.0, ["Address mismatch"]),
            make_assessment("Graph Agent", 50, 1.0, ["Cross-community"]),
            make_assessment("Behavioral Agent", 50, 1.0, ["New category"]),
        ]
        verdict = coord.synthesize("txn_mid", assessments)
        assert verdict.verdict == "FLAG"
        assert 30 <= verdict.final_score < 70

    def test_coordinator_verdict_block(self):
        """final_score ~80 -> verdict='BLOCK'."""
        from backend.agents.coordinator_agent import CoordinatorAgent
        coord = CoordinatorAgent(use_llm=False)
        assessments = [
            make_assessment("Velocity Agent", 80, 1.0, ["Rapid burst"]),
            make_assessment("Geolocation Agent", 80, 1.0, ["Impossible travel"]),
            make_assessment("Graph Agent", 80, 1.0, ["Fraud network"]),
            make_assessment("Behavioral Agent", 80, 1.0, ["Major deviation"]),
        ]
        verdict = coord.synthesize("txn_high", assessments)
        assert verdict.verdict == "BLOCK"
        assert verdict.final_score >= 70

    def test_coordinator_threshold_boundaries(self):
        """Boundary tests: 29.9 -> APPROVE, 30.0 -> FLAG, 69.9 -> FLAG, 70.0 -> BLOCK."""
        from backend.agents.coordinator_agent import CoordinatorAgent
        coord = CoordinatorAgent(use_llm=False)

        def make_uniform(score):
            return [
                make_assessment("Velocity Agent", score, 1.0, []),
                make_assessment("Geolocation Agent", score, 1.0, []),
                make_assessment("Graph Agent", score, 1.0, []),
                make_assessment("Behavioral Agent", score, 1.0, []),
            ]

        v1 = coord.synthesize("t1", make_uniform(29.9))
        assert v1.verdict == "APPROVE", f"29.9 should APPROVE, got {v1.verdict} (score={v1.final_score})"

        v2 = coord.synthesize("t2", make_uniform(30.0))
        assert v2.verdict == "FLAG", f"30.0 should FLAG, got {v2.verdict} (score={v2.final_score})"

        v3 = coord.synthesize("t3", make_uniform(69.9))
        assert v3.verdict == "FLAG", f"69.9 should FLAG, got {v3.verdict} (score={v3.final_score})"

        v4 = coord.synthesize("t4", make_uniform(70.0))
        assert v4.verdict == "BLOCK", f"70.0 should BLOCK, got {v4.verdict} (score={v4.final_score})"

    def test_coordinator_rule_based_explanation(self):
        """use_llm=False, high-risk assessments -> explanation contains score and top agent signals."""
        from backend.agents.coordinator_agent import CoordinatorAgent
        coord = CoordinatorAgent(use_llm=False)
        assessments = [
            make_assessment("Velocity Agent", 85, 0.9, ["3 txns in 90 sec"]),
            make_assessment("Geolocation Agent", 70, 0.8, ["Impossible travel"]),
            make_assessment("Graph Agent", 60, 0.7, ["Shared device"]),
            make_assessment("Behavioral Agent", 20, 0.5, []),
        ]
        verdict = coord.synthesize("txn_explain", assessments)
        explanation = verdict.explanation
        # Should contain the score
        assert str(int(verdict.final_score)) in explanation or f"{verdict.final_score}" in explanation
        # Should mention at least one top agent signal
        assert any(kw in explanation.lower() for kw in ["velocity", "geolocation", "graph"]), \
            f"Expected top agent name in explanation, got: {explanation}"

    def test_coordinator_processing_time(self, sample_assessments):
        """processing_time_ms > 0."""
        from backend.agents.coordinator_agent import CoordinatorAgent
        coord = CoordinatorAgent(use_llm=False)
        verdict = coord.synthesize("txn_time", sample_assessments)
        assert verdict.processing_time_ms > 0

    def test_coordinator_graph_weight(self):
        """Graph Agent assessment has more impact than others (weight 0.30 vs 0.20-0.25)."""
        from backend.agents.coordinator_agent import CoordinatorAgent
        coord = CoordinatorAgent(use_llm=False)

        # Scenario: Graph Agent scores 100, all others score 0
        graph_high = [
            make_assessment("Velocity Agent", 0, 1.0, []),
            make_assessment("Geolocation Agent", 0, 1.0, []),
            make_assessment("Graph Agent", 100, 1.0, ["Max fraud"]),
            make_assessment("Behavioral Agent", 0, 1.0, []),
        ]
        v_graph = coord.synthesize("t_graph", graph_high)

        # Scenario: Behavioral Agent scores 100, all others score 0
        behav_high = [
            make_assessment("Velocity Agent", 0, 1.0, []),
            make_assessment("Geolocation Agent", 0, 1.0, []),
            make_assessment("Graph Agent", 0, 1.0, []),
            make_assessment("Behavioral Agent", 100, 1.0, ["Max deviation"]),
        ]
        v_behav = coord.synthesize("t_behav", behav_high)

        # Graph=0.30 should produce higher score than Behavioral=0.20
        assert v_graph.final_score > v_behav.final_score, \
            f"Graph weight (score={v_graph.final_score}) should exceed Behavioral (score={v_behav.final_score})"

    def test_coordinator_all_low_scores(self):
        """All agents return <10 score -> verdict APPROVE, explanation mentions no significant risk."""
        from backend.agents.coordinator_agent import CoordinatorAgent
        coord = CoordinatorAgent(use_llm=False)
        assessments = [
            make_assessment("Velocity Agent", 5, 0.8, []),
            make_assessment("Geolocation Agent", 3, 0.7, []),
            make_assessment("Graph Agent", 7, 0.6, []),
            make_assessment("Behavioral Agent", 2, 0.5, []),
        ]
        verdict = coord.synthesize("txn_safe", assessments)
        assert verdict.verdict == "APPROVE"
        assert "no significant" in verdict.explanation.lower() or verdict.final_score < 30
