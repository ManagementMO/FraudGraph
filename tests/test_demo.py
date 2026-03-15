"""Tests for demo infrastructure: batch evaluation metrics and Gemini cache."""
import json
import tempfile
from pathlib import Path

import pytest

from backend.agents.coordinator_agent import CoordinatorAgent
from backend.models.schemas import AgentAssessment


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def eval_pipeline():
    """Module-scoped lightweight pipeline for evaluation tests (500 txns, no LLM)."""
    from backend.pipeline import FraudDetectionPipeline

    pipeline = FraudDetectionPipeline(sample_size=500, use_llm=False)
    pipeline.initialize()
    return pipeline


@pytest.fixture(scope="module")
def eval_results(eval_pipeline):
    """Run evaluation once and share results across tests."""
    from backend.demo.evaluate import run_evaluation

    return run_evaluation(eval_pipeline, n=50)


def _mock_assessments(graph_score: float = 50.0, other_score: float = 10.0) -> list[AgentAssessment]:
    """Create mock agent assessments with specified graph and other scores."""
    return [
        AgentAssessment(
            agent_name="Velocity Agent",
            risk_score=other_score,
            confidence=0.8,
            signals=["Normal velocity"],
            explanation="Low risk",
        ),
        AgentAssessment(
            agent_name="Geolocation Agent",
            risk_score=other_score,
            confidence=0.7,
            signals=["Known location"],
            explanation="Low risk",
        ),
        AgentAssessment(
            agent_name="Graph Agent",
            risk_score=graph_score,
            confidence=0.9,
            signals=["Connected to fraud cluster"],
            explanation="High graph risk",
        ),
        AgentAssessment(
            agent_name="Behavioral Agent",
            risk_score=other_score,
            confidence=0.6,
            signals=["Normal pattern"],
            explanation="Low risk",
        ),
    ]


# ── TestBatchEvaluation ──────────────────────────────────────────────


class TestBatchEvaluation:
    """Tests for DEMO-02: batch evaluation metrics."""

    def test_evaluate_returns_metrics(self, eval_results):
        """run_evaluation() returns dict with required metric keys."""
        required_keys = {"precision", "recall", "f1", "total", "fraud_count", "graph_highlights"}
        assert required_keys.issubset(eval_results.keys()), (
            f"Missing keys: {required_keys - eval_results.keys()}"
        )

    def test_metrics_are_valid_floats(self, eval_results):
        """Precision/recall/f1 are floats in [0, 1]."""
        for metric in ("precision", "recall", "f1"):
            val = eval_results[metric]
            assert isinstance(val, float), f"{metric} should be float, got {type(val)}"
            assert 0.0 <= val <= 1.0, f"{metric} should be in [0, 1], got {val}"

    def test_graph_highlights_structure(self, eval_results):
        """Graph highlights have required keys."""
        highlights = eval_results["graph_highlights"]
        assert isinstance(highlights, list)
        # Highlights may be empty if no graph-unique catches in 50 txns
        for h in highlights:
            required = {"transaction_id", "graph_score", "other_max_score", "verdict", "is_fraud"}
            assert required.issubset(h.keys()), f"Highlight missing keys: {required - h.keys()}"

    def test_flag_threshold_matches_coordinator(self):
        """Evaluation uses CoordinatorAgent.THRESHOLDS['FLAG'] == 30."""
        assert CoordinatorAgent.THRESHOLDS["FLAG"] == 30

    def test_total_matches_requested(self, eval_results):
        """Total evaluated matches the requested n."""
        assert eval_results["total"] == 50

    def test_report_string_present(self, eval_results):
        """Full classification report string is included."""
        assert "report" in eval_results
        assert isinstance(eval_results["report"], str)
        assert len(eval_results["report"]) > 0


# ── TestGeminiCache ──────────────────────────────────────────────────


class TestGeminiCache:
    """Tests for DEMO-03: cache loading in coordinator."""

    def test_coordinator_uses_cache(self):
        """CoordinatorAgent serves cached explanation when cache hit."""
        cache_data = {"test_txn": "cached explanation for test"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cache_data, f)
            tmp_path = f.name

        try:
            coord = CoordinatorAgent(use_llm=False, cache_path=tmp_path)
            assessments = _mock_assessments()
            verdict = coord.synthesize("test_txn", assessments)
            assert verdict.explanation == "cached explanation for test"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_coordinator_fallback_on_miss(self):
        """CoordinatorAgent falls back to rule-based when cache misses."""
        coord = CoordinatorAgent(use_llm=False, cache_path=None)
        assessments = _mock_assessments()
        verdict = coord.synthesize("unknown_txn", assessments)
        # Rule-based explanation should be a non-empty string
        assert isinstance(verdict.explanation, str)
        assert len(verdict.explanation) > 0

    def test_coordinator_no_cache_file(self):
        """CoordinatorAgent works when cache_path doesn't exist."""
        coord = CoordinatorAgent(use_llm=False, cache_path="/nonexistent/path.json")
        # Should not raise, cache should be empty
        assert coord._explanation_cache == {}
        assessments = _mock_assessments()
        verdict = coord.synthesize("any_txn", assessments)
        assert isinstance(verdict.explanation, str)
        assert len(verdict.explanation) > 0
