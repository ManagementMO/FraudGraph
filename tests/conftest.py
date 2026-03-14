"""Shared pytest fixtures for FraudGraph test suite."""
import pytest


@pytest.fixture
def synthetic_df():
    """Generate a 2000-row synthetic DataFrame for testing."""
    from backend.data.loader import generate_synthetic_data
    return generate_synthetic_data(2000)


@pytest.fixture
def sample_train_test(synthetic_df):
    """Return (train_df, test_df) from temporal split of synthetic data."""
    from backend.data.loader import load_and_split
    # Use synthetic data via load_and_split with a small sample
    train_df, test_df = load_and_split("nonexistent_dir", sample_size=2000)
    return train_df, test_df


@pytest.fixture
def transaction_graph(sample_train_test):
    """Build a TransactionGraph from the training split."""
    from backend.data.graph_builder import TransactionGraph
    train_df, _ = sample_train_test
    graph = TransactionGraph()
    graph.build_from_dataframe(train_df)
    return graph


# --- API / Server fixtures (session-scoped for speed) ---


@pytest.fixture(scope="session")
def test_pipeline():
    """Session-scoped lightweight pipeline for API tests (500 txns, no LLM)."""
    from backend.pipeline import FraudDetectionPipeline
    pipeline = FraudDetectionPipeline(sample_size=500, use_llm=False)
    pipeline.initialize()
    return pipeline


@pytest.fixture(scope="session")
def test_client(test_pipeline):
    """Session-scoped TestClient that reuses the lightweight pipeline."""
    from starlette.testclient import TestClient
    from backend.server import app
    # Set pipeline directly on app.state to skip lifespan's heavy loading
    app.state.pipeline = test_pipeline
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
