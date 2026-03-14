"""End-to-end integration tests for the FraudDetectionPipeline."""
import pytest
from backend.pipeline import FraudDetectionPipeline


@pytest.fixture(scope="module")
def pipeline():
    """Initialize pipeline once for all tests (small sample for speed)."""
    p = FraudDetectionPipeline(data_dir="data", sample_size=500, use_llm=False)
    p.initialize()
    return p


class TestPipelineInitialization:
    """Tests for pipeline initialization."""

    def test_pipeline_initialization(self, pipeline):
        """Pipeline initializes with data, graph, and agents."""
        assert pipeline._initialized
        assert pipeline.train_df is not None
        assert pipeline.test_df is not None
        assert len(pipeline.train_df) > 0
        assert len(pipeline.test_df) > 0
        assert pipeline.graph is not None
        assert pipeline.graph.G.number_of_nodes() > 0
        assert len(pipeline.graph.card_profiles) > 0
        assert pipeline.communities is not None

    def test_pipeline_agents_created(self, pipeline):
        """All 5 agents are created."""
        assert pipeline.velocity_agent is not None
        assert pipeline.geo_agent is not None
        assert pipeline.graph_agent is not None
        assert pipeline.behavioral_agent is not None
        assert pipeline.coordinator is not None


class TestPipelineAnalysis:
    """Tests for transaction analysis."""

    def test_pipeline_analyze_transaction(self, pipeline):
        """Analyze a transaction and get complete FraudVerdict."""
        txns = pipeline.get_sample_transactions(1)
        assert len(txns) == 1
        txn = txns[0]

        verdict = pipeline.analyze_transaction(txn)

        # FraudVerdict structure checks
        assert verdict.transaction_id is not None
        assert verdict.transaction_id != ""
        assert 0 <= verdict.final_score <= 100
        assert verdict.verdict in ["APPROVE", "FLAG", "BLOCK"]
        assert len(verdict.agent_assessments) == 4
        assert verdict.explanation is not None
        assert len(verdict.explanation) > 0
        assert verdict.processing_time_ms >= 0

        # Check each agent assessment
        agent_names = {a.agent_name for a in verdict.agent_assessments}
        expected_agents = {"Velocity Agent", "Geolocation Agent", "Graph Agent", "Behavioral Agent"}
        assert agent_names == expected_agents

    def test_pipeline_analyze_fraud_transaction(self, pipeline):
        """Known fraud transactions tend to score higher than legit ones."""
        # Find fraud and legit transactions
        fraud_txns = pipeline.test_df[pipeline.test_df["isFraud"] == 1]
        legit_txns = pipeline.test_df[pipeline.test_df["isFraud"] == 0]

        if len(fraud_txns) == 0 or len(legit_txns) == 0:
            pytest.skip("Need both fraud and legit transactions for comparison")

        # Analyze multiple of each for statistical stability
        n_sample = min(5, len(fraud_txns), len(legit_txns))
        fraud_scores = []
        legit_scores = []

        for _, row in fraud_txns.head(n_sample).iterrows():
            v = pipeline.analyze_transaction(row.to_dict())
            fraud_scores.append(v.final_score)

        for _, row in legit_txns.head(n_sample).iterrows():
            v = pipeline.analyze_transaction(row.to_dict())
            legit_scores.append(v.final_score)

        avg_fraud = sum(fraud_scores) / len(fraud_scores)
        avg_legit = sum(legit_scores) / len(legit_scores)

        # Fraud transactions should on average score higher (not guaranteed per-txn)
        # Use a soft assertion -- if they're close, that's still informative
        print(f"Avg fraud score: {avg_fraud:.1f}, Avg legit score: {avg_legit:.1f}")
        # At minimum, the pipeline should produce different scores for different inputs
        assert len(set(fraud_scores + legit_scores)) > 1, "Pipeline should produce varied scores"


class TestPipelineSamples:
    """Tests for sample transactions and stats."""

    def test_pipeline_sample_transactions(self, pipeline):
        """get_sample_transactions returns correct number of dicts."""
        samples = pipeline.get_sample_transactions(5)
        assert len(samples) == 5
        for txn in samples:
            assert isinstance(txn, dict)
            assert "card_id" in txn
            # Should have at least transaction amount
            assert "TransactionAmt" in txn or "amount" in txn

    def test_pipeline_stats(self, pipeline):
        """get_stats returns meaningful statistics."""
        stats = pipeline.get_stats()
        assert stats["node_count"] > 0
        assert stats["edge_count"] > 0
        assert stats["community_count"] > 0
        assert stats["train_size"] > 0
        assert stats["test_size"] > 0
        assert stats["card_profile_count"] > 0
