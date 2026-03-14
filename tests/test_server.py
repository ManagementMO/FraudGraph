"""Integration tests for the FraudGraph FastAPI server endpoints."""
import math


class TestHealthEndpoint:
    """GET /health returns 200 with status healthy."""

    def test_health_endpoint(self, test_client):
        resp = test_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["pipeline_initialized"] is True


class TestAnalyzeEndpoint:
    """POST /analyze returns a complete FraudVerdict."""

    def test_analyze_returns_verdict(self, test_client):
        resp = test_client.post("/analyze", json={
            "amount": 9999.0,
            "card_id": "card_1_visa_debit",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["verdict"] in ("APPROVE", "FLAG", "BLOCK")
        assert len(data["agent_assessments"]) == 4

    def test_analyze_has_required_fields(self, test_client):
        resp = test_client.post("/analyze", json={
            "amount": 500.0,
            "card_id": "card_1_visa_debit",
        })
        assert resp.status_code == 200
        data = resp.json()
        required = [
            "transaction_id",
            "final_score",
            "verdict",
            "agent_assessments",
            "explanation",
            "processing_time_ms",
        ]
        for field in required:
            assert field in data, f"Missing required field: {field}"


class TestStatsEndpoint:
    """GET /stats returns dashboard metrics."""

    def test_stats_endpoint(self, test_client):
        resp = test_client.get("/stats")
        assert resp.status_code == 200
        data = resp.json()
        for key in ("node_count", "edge_count", "train_size", "test_size", "total_transactions"):
            assert key in data, f"Missing stats field: {key}"
        assert data["total_transactions"] == data["train_size"] + data["test_size"]


class TestGraphEndpoint:
    """GET /graph/{card_id} returns D3-compatible subgraph JSON."""

    def test_graph_endpoint(self, test_client):
        resp = test_client.get("/graph/card_1_visa_debit")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "links" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["links"], list)
        # Each node should have required keys
        if data["nodes"]:
            node = data["nodes"][0]
            for key in ("id", "type", "is_fraud"):
                assert key in node, f"Node missing key: {key}"

    def test_graph_max_nodes(self, test_client):
        resp = test_client.get("/graph/card_1_visa_debit?max_nodes=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["nodes"]) <= 5

    def test_graph_unknown_card(self, test_client):
        resp = test_client.get("/graph/nonexistent_card_xyz_999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["nodes"] == []
        assert data["links"] == []


class TestSampleTransactionsEndpoint:
    """GET /sample-transactions returns sanitized sample data."""

    def test_sample_transactions(self, test_client):
        resp = test_client.get("/sample-transactions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Each item should have basic transaction fields
        item = data[0]
        assert "card_id" in item
        assert "amount" in item or "TransactionAmt" in item

    def test_sample_transactions_no_nan(self, test_client):
        resp = test_client.get("/sample-transactions")
        assert resp.status_code == 200
        data = resp.json()
        for i, txn in enumerate(data):
            for key, val in txn.items():
                if isinstance(val, float):
                    assert not math.isnan(val), f"NaN found in txn[{i}][{key}]"
                    assert not math.isinf(val), f"Inf found in txn[{i}][{key}]"
