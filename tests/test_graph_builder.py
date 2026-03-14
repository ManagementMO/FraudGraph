"""Tests for TransactionGraph: construction, profiles, communities, and export."""
import pytest


class TestBuildGraph:
    """Tests for graph construction from DataFrame."""

    def test_build_graph_nodes(self, transaction_graph):
        """Graph has card, merchant, and device typed nodes."""
        node_types = set()
        for _, data in transaction_graph.G.nodes(data=True):
            node_types.add(data.get("type"))
        assert "card" in node_types, "Missing card nodes"
        assert "merchant" in node_types, "Missing merchant nodes"
        assert "device" in node_types, "Missing device nodes"

    def test_build_graph_edges(self, transaction_graph):
        """Edges exist between cards and merchants/devices."""
        assert transaction_graph.G.number_of_edges() > 0, "No edges in graph"
        # Check at least one card-merchant edge exists
        found_card_merchant = False
        for u, v in transaction_graph.G.edges():
            u_type = transaction_graph.G.nodes[u].get("type")
            v_type = transaction_graph.G.nodes[v].get("type")
            if {u_type, v_type} == {"card", "merchant"}:
                found_card_merchant = True
                break
        assert found_card_merchant, "No card-merchant edges found"

    def test_build_graph_has_nodes(self, transaction_graph):
        """Graph has a non-trivial number of nodes."""
        assert transaction_graph.G.number_of_nodes() > 10, "Too few nodes in graph"


class TestCardProfiles:
    """Tests for card spending profiles."""

    def test_card_profiles_exist(self, transaction_graph):
        """Card profiles dict is populated."""
        assert len(transaction_graph.card_profiles) > 0, "No card profiles built"

    def test_card_profiles_have_expected_keys(self, transaction_graph):
        """Profiles have amounts, timestamps, merchants, categories keys."""
        for card_id, profile in list(transaction_graph.card_profiles.items())[:5]:
            assert "amounts" in profile, f"Missing 'amounts' in profile for {card_id}"
            assert "timestamps" in profile, f"Missing 'timestamps' in profile for {card_id}"
            assert "merchants" in profile, f"Missing 'merchants' in profile for {card_id}"
            assert "categories" in profile, f"Missing 'categories' in profile for {card_id}"

    def test_card_profiles_amounts_populated(self, transaction_graph):
        """At least some profiles have non-empty amounts lists."""
        non_empty = sum(
            1 for p in transaction_graph.card_profiles.values()
            if len(p["amounts"]) > 0
        )
        assert non_empty > 0, "No profiles have amounts"


class TestCommunityDetection:
    """Tests for Louvain community detection."""

    def test_detect_communities_returns_mapping(self, transaction_graph):
        """detect_communities returns dict mapping node -> community_id."""
        communities = transaction_graph.detect_communities()
        assert isinstance(communities, dict)
        assert len(communities) > 0, "Empty community mapping"

    def test_detect_communities_covers_nodes(self, transaction_graph):
        """Community mapping has entries for nodes in graph."""
        communities = transaction_graph.detect_communities()
        graph_nodes = set(transaction_graph.G.nodes())
        community_nodes = set(communities.keys())
        assert community_nodes == graph_nodes, "Community mapping doesn't cover all nodes"


class TestFraudExposure:
    """Tests for fraud exposure calculation."""

    def test_get_fraud_exposure_returns_dict(self, transaction_graph):
        """get_fraud_exposure returns dict with expected keys."""
        card_id = list(transaction_graph.card_profiles.keys())[0]
        exposure = transaction_graph.get_fraud_exposure(card_id)
        assert isinstance(exposure, dict)
        assert "exposure_score" in exposure
        assert "fraud_neighbors" in exposure

    def test_get_fraud_exposure_score_range(self, transaction_graph):
        """Exposure score is between 0 and 100."""
        card_id = list(transaction_graph.card_profiles.keys())[0]
        exposure = transaction_graph.get_fraud_exposure(card_id)
        assert 0 <= exposure["exposure_score"] <= 100

    def test_get_fraud_exposure_unknown_card(self, transaction_graph):
        """Unknown card returns zero exposure."""
        exposure = transaction_graph.get_fraud_exposure("nonexistent_card_xyz")
        assert exposure["exposure_score"] == 0


class TestGraphDataForFrontend:
    """Tests for D3.js export."""

    def test_get_graph_data_for_frontend_structure(self, transaction_graph):
        """get_graph_data_for_frontend returns dict with nodes and links lists."""
        card_id = list(transaction_graph.card_profiles.keys())[0]
        data = transaction_graph.get_graph_data_for_frontend(card_id)
        assert isinstance(data, dict)
        assert "nodes" in data
        assert "links" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["links"], list)

    def test_get_graph_data_for_frontend_has_content(self, transaction_graph):
        """Export includes nodes and links for a known card."""
        card_id = list(transaction_graph.card_profiles.keys())[0]
        data = transaction_graph.get_graph_data_for_frontend(card_id, depth=1)
        assert len(data["nodes"]) > 0, "No nodes in frontend export"

    def test_get_graph_data_for_frontend_unknown_card(self, transaction_graph):
        """Unknown card returns empty nodes and links."""
        data = transaction_graph.get_graph_data_for_frontend("nonexistent_card_xyz")
        assert data["nodes"] == []
        assert data["links"] == []
