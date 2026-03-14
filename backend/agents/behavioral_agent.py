"""
Behavioral Agent: Compares transaction against historical behavioral profile.

Analyzes:
- New/rare category (Counter-based, <5% frequency = rare)
- Amount deviation within category (z-score >2.5)
- New merchant (not in historical merchant list)
- Thin-history accounts (<3 txns) with high amounts (>$200) get moderate score
"""
import numpy as np
from collections import Counter
from backend.models.schemas import AgentAssessment


class BehavioralAgent:
    """
    Compares transaction against historical behavioral profile:
    - Spending category changes
    - Amount deviations within category
    - New merchant patterns
    """

    def __init__(self, card_profiles: dict):
        self.card_profiles = card_profiles

    def analyze(self, transaction: dict) -> AgentAssessment:
        card_id = transaction.get("card_id", "unknown")
        amount = float(
            transaction.get("amount", transaction.get("TransactionAmt", 0))
        )
        category = transaction.get(
            "product_category", transaction.get("ProductCD", "Unknown")
        )
        merchant_id = transaction.get("merchant_id", "unknown")

        signals = []
        risk_scores = []
        profile = self.card_profiles.get(card_id, {})

        if profile and len(profile.get("amounts", [])) >= 3:
            categories = profile.get("categories", [])
            merchants = profile.get("merchants", [])
            amounts = profile["amounts"]
            cat_counts = Counter(categories)
            total_txns = len(categories)

            # 1. New/rare category
            if category not in cat_counts:
                top_cats = [c for c, _ in cat_counts.most_common(3)]
                signals.append(
                    f"First-ever '{category}' transaction (usual: {', '.join(top_cats)})"
                )
                risk_scores.append(30)
            elif total_txns > 0 and cat_counts[category] / total_txns < 0.05:
                signals.append(
                    f"Rare category '{category}' ({cat_counts[category]}/{total_txns} historical)"
                )
                risk_scores.append(20)

            # 2. Amount deviation within category
            cat_amts = [
                amounts[i]
                for i in range(min(len(amounts), len(categories)))
                if categories[i] == category
            ]
            if len(cat_amts) >= 3:
                cat_mean = np.mean(cat_amts)
                cat_std = np.std(cat_amts) + 1e-6
                z = (amount - cat_mean) / cat_std
                if z > 2.5:
                    signals.append(
                        f"${amount:.2f} is {z:.1f}x above avg for '{category}' (avg ${cat_mean:.2f})"
                    )
                    risk_scores.append(min(z * 12, 70))

            # 3. New merchant
            if merchant_id not in Counter(merchants):
                signals.append(
                    f"First transaction with {merchant_id[:30]} ({len(set(merchants))} prior merchants)"
                )
                risk_scores.append(15)
        else:
            # Thin-history or unknown card
            if amount > 200:
                signals.append(
                    f"${amount:.2f} on thin-history account ({len(profile.get('amounts', []))} prior txns)"
                )
                risk_scores.append(25)

        final_score = (
            min(max(risk_scores) * 0.6 + np.mean(risk_scores) * 0.4, 100)
            if risk_scores
            else 5.0
        )
        confidence = min(0.4 + len(signals) * 0.15, 0.85)

        return AgentAssessment(
            agent_name="Behavioral Agent",
            risk_score=round(float(final_score), 1),
            confidence=round(confidence, 2),
            signals=signals,
            explanation=(
                f"Behavioral analysis: {'; '.join(signals)}"
                if signals
                else "Behavioral analysis: Consistent with history."
            ),
        )
