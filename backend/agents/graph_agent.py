"""
Graph Agent: Analyzes the transaction graph for network-level fraud.

This is the highest-weighted agent (0.30) -- the core differentiator of FraudGraph.

Analyzes:
- Fraud exposure via shared device fingerprints with known fraud accounts
- Community detection (cross-community transactions between card and merchant)
- Node degree analysis (high connectivity = card testing patterns)
"""
from backend.models.schemas import AgentAssessment


class GraphAgent:
    """
    Analyzes the transaction graph for network-level fraud:
    - Shared device fingerprints with known fraud accounts
    - Community detection (fraud clusters)
    - Node degree analysis (card testing patterns)
    """

    def __init__(self, transaction_graph):
        self.graph = transaction_graph
        self._communities = None

    def _ensure_communities(self):
        """Lazily compute communities. Supports pre-set _communities for startup perf."""
        if self._communities is None:
            self._communities = self.graph.detect_communities()

    def analyze(self, transaction: dict) -> AgentAssessment:
        card_id = transaction.get("card_id", "unknown")
        merchant_id = transaction.get("merchant_id", "unknown")

        signals = []
        risk_scores = []

        # 1. Fraud exposure through graph
        exposure = self.graph.get_fraud_exposure(card_id)
        if exposure["exposure_score"] > 0:
            signals.append(f"Graph exposure: {exposure['exposure_score']}/100")
            risk_scores.append(exposure["exposure_score"])
            if exposure["shared_device_cards"] > 0:
                signals.append(
                    f"Shares device with {exposure['shared_device_cards']} other cards"
                )
            if exposure["fraud_neighbors"] > 0:
                signals.append(exposure["details"])

        # 2. Community analysis
        self._ensure_communities()
        card_comm = self._communities.get(card_id)
        merchant_comm = self._communities.get(merchant_id)
        if (
            card_comm is not None
            and merchant_comm is not None
            and card_comm != merchant_comm
        ):
            signals.append(
                f"Cross-community transaction (card={card_comm}, merchant={merchant_comm})"
            )
            risk_scores.append(15)

        # 3. Node degree (high connectivity = suspicious)
        if card_id in self.graph.G:
            degree = self.graph.G.degree(card_id)
            neighbors = self.graph.get_card_neighbors(card_id)
            n_merchants = len(neighbors["merchants"])

            if degree > 50:
                signals.append(f"High connectivity: {degree} connections")
                risk_scores.append(40)
            if n_merchants > 20:
                signals.append(
                    f"Used at {n_merchants} merchants (potential card testing)"
                )
                risk_scores.append(35)

        final_score = (
            min(
                max(risk_scores) * 0.6 + sum(risk_scores) / len(risk_scores) * 0.4,
                100,
            )
            if risk_scores
            else 5.0
        )
        confidence = min(0.5 + len(signals) * 0.1, 0.85)

        return AgentAssessment(
            agent_name="Graph Agent",
            risk_score=round(float(final_score), 1),
            confidence=round(confidence, 2),
            signals=signals,
            explanation=(
                f"Graph analysis: {'; '.join(signals)}"
                if signals
                else "Graph analysis: No network anomalies."
            ),
        )
