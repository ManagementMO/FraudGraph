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


class TestWebSocketStream:
    """WebSocket /ws/stream streams agent assessments and final verdict."""

    def test_websocket_streams_assessments(self, test_client):
        """Connect, send transaction, receive 5 messages (4 assessments + 1 verdict)."""
        with test_client.websocket_connect("/ws/stream") as ws:
            ws.send_json({"amount": 5000.0, "card_id": "card_1_visa_debit"})
            messages = [ws.receive_json() for _ in range(5)]

            assessment_msgs = [m for m in messages if m["type"] == "agent_assessment"]
            verdict_msgs = [m for m in messages if m["type"] == "final_verdict"]

            assert len(assessment_msgs) == 4, f"Expected 4 assessments, got {len(assessment_msgs)}"
            assert len(verdict_msgs) == 1, f"Expected 1 verdict, got {len(verdict_msgs)}"

    def test_websocket_agent_order(self, test_client):
        """Agent assessments arrive in locked order: Velocity, Geo, Graph, Behavioral."""
        with test_client.websocket_connect("/ws/stream") as ws:
            ws.send_json({"amount": 5000.0, "card_id": "card_1_visa_debit"})
            messages = [ws.receive_json() for _ in range(5)]

            assessment_msgs = [m for m in messages if m["type"] == "agent_assessment"]
            agent_names = [m["data"]["agent_name"] for m in assessment_msgs]

            expected_order = ["VelocityAgent", "GeolocationAgent", "GraphAgent", "BehavioralAgent"]
            assert agent_names == expected_order, f"Agent order {agent_names} != {expected_order}"

    def test_websocket_verdict_fields(self, test_client):
        """Final verdict contains required fields."""
        with test_client.websocket_connect("/ws/stream") as ws:
            ws.send_json({"amount": 5000.0, "card_id": "card_1_visa_debit"})
            messages = [ws.receive_json() for _ in range(5)]

            verdict_msg = [m for m in messages if m["type"] == "final_verdict"][0]
            data = verdict_msg["data"]

            assert data["verdict"] in ("APPROVE", "FLAG", "BLOCK"), f"Invalid verdict: {data['verdict']}"
            assert "final_score" in data
            assert isinstance(data["agent_assessments"], list)
            assert len(data["agent_assessments"]) == 4
            assert "explanation" in data

    def test_websocket_error_recovery(self, test_client):
        """Malformed JSON produces error message, not a crash."""
        with test_client.websocket_connect("/ws/stream") as ws:
            ws.send_text("not_json")
            msg = ws.receive_json()

            assert msg["type"] == "error", f"Expected error type, got {msg['type']}"
            assert "message" in msg["data"]
