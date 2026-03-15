"""
NetworkX graph construction for fraud detection.

Provides:
- TransactionGraph: Heterogeneous graph with card, merchant, device nodes
  connected by weighted transaction edges. Includes card spending profiles,
  Louvain community detection, fraud exposure scoring, and D3.js export.
"""
import networkx as nx
import pandas as pd
import numpy as np
from collections import Counter


class TransactionGraph:
    """
    Heterogeneous transaction graph:
    - Nodes: cards, merchants, devices (typed)
    - Edges: transactions connecting entities
    - Enables network-level fraud detection (the core innovation)
    """

    def __init__(self):
        self.G = nx.Graph()
        self.card_profiles: dict = {}

    def build_from_dataframe(self, df: pd.DataFrame) -> "TransactionGraph":
        """Build the full transaction graph from the dataset."""

        for row in df.itertuples(index=False):
            txn_id = str(getattr(row, "TransactionID", ""))
            card_id = str(row.card_id)
            merchant_id = str(getattr(row, "merchant_id", "unknown"))
            device_id = str(getattr(row, "device_id", "unknown_device"))
            amount = float(getattr(row, "TransactionAmt", getattr(row, "amount", 0)))
            is_fraud = int(getattr(row, "isFraud", 0))
            timestamp = float(getattr(row, "TransactionDT", getattr(row, "timestamp", 0)))
            category = str(getattr(row, "ProductCD", getattr(row, "product_category", "Unknown")))

            # Add typed nodes
            if card_id not in self.G:
                self.G.add_node(card_id, type="card")
            if merchant_id != "unknown":
                if merchant_id not in self.G:
                    self.G.add_node(merchant_id, type="merchant")

                # Card <-> Merchant edge
                if self.G.has_edge(card_id, merchant_id):
                    self.G[card_id][merchant_id]["weight"] += 1
                    self.G[card_id][merchant_id]["total_amount"] += amount
                else:
                    self.G.add_edge(card_id, merchant_id, weight=1, total_amount=amount)

            # Card <-> Device edge (shared device = strong fraud signal)
            if device_id not in ("unknown_device", "nan", "None"):
                if device_id not in self.G:
                    self.G.add_node(device_id, type="device")
                if self.G.has_edge(card_id, device_id):
                    self.G[card_id][device_id]["weight"] += 1
                else:
                    self.G.add_edge(card_id, device_id, weight=1)

            # Build per-card spending profiles
            if card_id not in self.card_profiles:
                self.card_profiles[card_id] = {
                    "amounts": [],
                    "timestamps": [],
                    "merchants": [],
                    "categories": [],
                    "fraud_count": 0,
                    "last_addr1": None,
                    "last_device_type": None,
                }

            p = self.card_profiles[card_id]
            p["amounts"].append(amount)
            p["timestamps"].append(timestamp)
            p["merchants"].append(merchant_id)
            p["categories"].append(category)
            if is_fraud:
                p["fraud_count"] += 1

        print(f"Graph built: {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")
        return self

    def get_card_neighbors(self, card_id: str) -> dict:
        """Get all entities connected to a card."""
        if card_id not in self.G:
            return {"merchants": [], "devices": [], "shared_device_cards": []}

        merchants, devices, shared_cards = [], [], []
        for neighbor in self.G.neighbors(card_id):
            ntype = self.G.nodes[neighbor].get("type", "unknown")
            if ntype == "merchant":
                merchants.append(neighbor)
            elif ntype == "device":
                devices.append(neighbor)
                for dn in self.G.neighbors(neighbor):
                    if dn != card_id and self.G.nodes.get(dn, {}).get("type") == "card":
                        shared_cards.append(dn)

        return {
            "merchants": merchants,
            "devices": devices,
            "shared_device_cards": list(set(shared_cards)),
        }

    def detect_communities(self) -> dict:
        """Louvain community detection -- finds transaction clusters."""
        from networkx.algorithms.community import louvain_communities
        communities = louvain_communities(self.G, seed=42)
        mapping = {}
        for i, comm in enumerate(communities):
            for node in comm:
                mapping[node] = i
        return mapping

    def get_fraud_exposure(self, card_id: str) -> dict:
        """Calculate how connected a card is to known fraud."""
        if card_id not in self.G:
            return {
                "exposure_score": 0,
                "fraud_neighbors": 0,
                "shared_device_cards": 0,
                "details": "Card not in graph",
            }

        neighbors = self.get_card_neighbors(card_id)
        fraud_connections = 0
        details = []

        # Check shared-device cards for fraud history
        for sc in neighbors["shared_device_cards"]:
            prof = self.card_profiles.get(sc, {})
            if prof.get("fraud_count", 0) > 0:
                fraud_connections += 1
                details.append(f"Shares device with {sc} ({prof['fraud_count']} fraud txns)")

        # Check merchant fraud rate
        for m in neighbors["merchants"]:
            m_cards = [
                n for n in self.G.neighbors(m)
                if self.G.nodes.get(n, {}).get("type") == "card"
            ]
            f_cards = sum(
                1 for c in m_cards
                if self.card_profiles.get(c, {}).get("fraud_count", 0) > 0
            )
            if m_cards:
                rate = f_cards / len(m_cards)
                if rate > 0.1:
                    details.append(f"Merchant {m} has {rate * 100:.1f}% fraud rate")
                    fraud_connections += 1

        return {
            "exposure_score": min(fraud_connections * 25, 100),
            "fraud_neighbors": fraud_connections,
            "shared_device_cards": len(neighbors["shared_device_cards"]),
            "details": "; ".join(details) if details else "No fraud connections detected",
        }

    def get_graph_data_for_frontend(self, card_id: str, depth: int = 2, communities: dict = None) -> dict:
        """Export subgraph around a card as JSON for D3.js visualization."""
        if card_id not in self.G:
            return {"nodes": [], "links": []}

        visited = {card_id}
        queue = [(card_id, 0)]
        nodes_to_include = set()

        while queue:
            current, d = queue.pop(0)
            nodes_to_include.add(current)
            if d < depth:
                for nb in self.G.neighbors(current):
                    if nb not in visited:
                        visited.add(nb)
                        queue.append((nb, d + 1))

        node_list = []
        for node in nodes_to_include:
            nd = self.G.nodes[node]
            is_fraud = self.card_profiles.get(node, {}).get("fraud_count", 0) > 0
            node_list.append({
                "id": node,
                "type": nd.get("type", "unknown"),
                "is_fraud": is_fraud,
                "is_target": node == card_id,
                "community": communities.get(node, 0) if communities else 0,
            })

        link_list = []
        for u, v, data in self.G.subgraph(nodes_to_include).edges(data=True):
            link_list.append({
                "source": u,
                "target": v,
                "weight": data.get("weight", 1),
            })

        return {"nodes": node_list, "links": link_list}
