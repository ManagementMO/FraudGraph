"""
End-to-end fraud detection pipeline.

Encapsulates the entire flow: data loading -> graph construction ->
agent analysis -> coordinator verdict. Designed for testing and future API use.

Usage:
    pipeline = FraudDetectionPipeline(data_dir="data", sample_size=1000, use_llm=False)
    pipeline.initialize()
    txn = pipeline.get_sample_transactions(1)[0]
    verdict = pipeline.analyze_transaction(txn)
    print(verdict)
"""
import time
import pandas as pd
from backend.data.loader import load_and_split
from backend.data.graph_builder import TransactionGraph
from backend.agents.velocity_agent import VelocityAgent
from backend.agents.geolocation_agent import GeolocationAgent
from backend.agents.graph_agent import GraphAgent
from backend.agents.behavioral_agent import BehavioralAgent
from backend.agents.coordinator_agent import CoordinatorAgent


def normalize_transaction(txn: dict) -> dict:
    """
    Normalize a transaction dict to handle both IEEE-CIS and custom field names.

    Maps IEEE-CIS column names to the standard names agents expect, while
    keeping original keys as fallbacks.
    """
    normalized = dict(txn)  # Copy to avoid mutating original

    # Map IEEE-CIS names -> standard names (only if standard name not present)
    mappings = {
        "TransactionAmt": "amount",
        "TransactionDT": "timestamp",
        "ProductCD": "product_category",
        "DeviceType": "device_type",
    }
    for ieee_name, standard_name in mappings.items():
        if standard_name not in normalized and ieee_name in normalized:
            normalized[standard_name] = normalized[ieee_name]

    # Ensure transaction_id exists
    if "transaction_id" not in normalized:
        tid = normalized.get("TransactionID", normalized.get("card_id", "unknown"))
        normalized["transaction_id"] = str(tid)

    return normalized


class FraudDetectionPipeline:
    """
    End-to-end fraud detection pipeline.

    Initializes data, builds graph, creates all agents, and provides
    analyze_transaction() to process individual transactions.
    """

    def __init__(self, data_dir: str = "data", sample_size: int = 15000, use_llm: bool = False):
        """
        Initialize pipeline configuration.

        Args:
            data_dir: Directory containing IEEE-CIS CSV files (or uses synthetic fallback)
            sample_size: Number of transactions to load
            use_llm: Whether to use Gemini for explanations (default False for safe batch use)
        """
        self.data_dir = data_dir
        self.sample_size = sample_size
        self.use_llm = use_llm

        # Will be populated by initialize()
        self.train_df: pd.DataFrame = None
        self.test_df: pd.DataFrame = None
        self.graph: TransactionGraph = None
        self.communities: dict = None
        self.velocity_agent: VelocityAgent = None
        self.geo_agent: GeolocationAgent = None
        self.graph_agent: GraphAgent = None
        self.behavioral_agent: BehavioralAgent = None
        self.coordinator: CoordinatorAgent = None
        self._initialized = False

    def initialize(self) -> None:
        """
        Load data with temporal split, build graph, detect communities, create agents.

        Must be called before analyze_transaction().
        """
        # 1. Load and split data temporally
        self.train_df, self.test_df = load_and_split(self.data_dir, self.sample_size)

        # 2. Build transaction graph from training data
        self.graph = TransactionGraph()
        self.graph.build_from_dataframe(self.train_df)

        # 3. Pre-compute communities at startup
        self.communities = self.graph.detect_communities()

        # 4. Create all 5 agents
        card_profiles = self.graph.card_profiles

        self.velocity_agent = VelocityAgent(card_profiles)
        self.geo_agent = GeolocationAgent(card_profiles)
        self.graph_agent = GraphAgent(self.graph)
        self.graph_agent._communities = self.communities  # Pre-set for performance
        self.behavioral_agent = BehavioralAgent(card_profiles)
        self.coordinator = CoordinatorAgent(use_llm=self.use_llm)

        self._initialized = True
        print(f"Pipeline initialized: {len(self.train_df)} train, {len(self.test_df)} test, "
              f"{self.graph.G.number_of_nodes()} graph nodes, "
              f"{len(self.communities)} communities mapped")

    def analyze_transaction(self, transaction: dict) -> "FraudVerdict":
        """
        Run all agents on a single transaction and return the final verdict.

        Args:
            transaction: Dict with transaction fields (IEEE-CIS or standard names)

        Returns:
            FraudVerdict with all fields populated
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")

        txn = normalize_transaction(transaction)
        txn_id = txn.get("transaction_id", str(txn.get("TransactionID", "unknown")))

        # Run 4 worker agents sequentially
        assessments = [
            self.velocity_agent.analyze(txn),
            self.geo_agent.analyze(txn),
            self.graph_agent.analyze(txn),
            self.behavioral_agent.analyze(txn),
        ]

        # Coordinator synthesizes final verdict
        verdict = self.coordinator.synthesize(txn_id, assessments)
        return verdict

    def get_sample_transactions(self, n: int = 10) -> list[dict]:
        """
        Return n sample transactions from test_df for demo/API use.

        Args:
            n: Number of sample transactions to return

        Returns:
            List of transaction dicts
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")

        n = min(n, len(self.test_df))
        sample = self.test_df.sample(n, random_state=42)
        return sample.to_dict(orient="records")

    def get_stats(self) -> dict:
        """
        Return pipeline statistics for dashboard/API use.

        Returns:
            Dict with graph_nodes, graph_edges, community_count, train_size, test_size, etc.
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")

        return {
            "node_count": self.graph.G.number_of_nodes(),
            "edge_count": self.graph.G.number_of_edges(),
            "community_count": len(set(self.communities.values())),
            "train_size": len(self.train_df),
            "test_size": len(self.test_df),
            "card_profile_count": len(self.graph.card_profiles),
            "fraud_rate_train": float(self.train_df["isFraud"].mean()) if "isFraud" in self.train_df.columns else None,
            "fraud_rate_test": float(self.test_df["isFraud"].mean()) if "isFraud" in self.test_df.columns else None,
        }
