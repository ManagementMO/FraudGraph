"""
Velocity Agent: Detects transaction frequency and amount anomalies.

Analyzes:
- Amount z-score vs historical baseline (z>3 = high, z>2 = moderate)
- Rapid burst detection (3+ transactions in 5-minute window)
- Night-time transaction anomaly (hour <5 or >23 with low night history)
"""
import numpy as np
from backend.models.schemas import AgentAssessment


class VelocityAgent:
    """
    Detects transaction frequency anomalies:
    - Rapid burst transactions (multiple in short time window)
    - Amount spikes vs historical baseline
    - Unusual time-of-day patterns
    """

    def __init__(self, card_profiles: dict):
        self.card_profiles = card_profiles

    def analyze(self, transaction: dict) -> AgentAssessment:
        card_id = transaction.get("card_id", "unknown")
        amount = float(transaction.get("amount", transaction.get("TransactionAmt", 0)))
        timestamp = float(transaction.get("timestamp", transaction.get("TransactionDT", 0)))
        hour = float(transaction.get("hour_of_day", 12))

        signals = []
        risk_scores = []
        profile = self.card_profiles.get(card_id)

        if profile and len(profile["amounts"]) >= 5:
            amounts = np.array(profile["amounts"])
            timestamps = np.array(profile["timestamps"])

            # 1. Amount Z-score
            mean_amt = amounts.mean()
            std_amt = amounts.std() + 1e-6
            z_score = (amount - mean_amt) / std_amt

            if z_score > 3:
                signals.append(
                    f"Amount ${amount:.2f} is {z_score:.1f} std devs above average (${mean_amt:.2f})"
                )
                risk_scores.append(min(z_score * 15, 95))
            elif z_score > 2:
                signals.append(
                    f"Amount ${amount:.2f} is elevated ({z_score:.1f}\u03c3 above ${mean_amt:.2f} avg)"
                )
                risk_scores.append(z_score * 12)

            # 2. Velocity burst (5-minute window)
            if timestamp > 0 and len(timestamps) > 0:
                recent_count = int(((timestamp - timestamps) < 300).sum())
                if recent_count >= 3:
                    signals.append(
                        f"{recent_count} transactions in last 5 minutes (rapid burst)"
                    )
                    risk_scores.append(min(recent_count * 20, 90))
                elif recent_count >= 2:
                    signals.append(f"{recent_count} transactions in last 5 minutes")
                    risk_scores.append(recent_count * 15)

            # 3. Night-time anomaly
            if hour < 5 or hour > 23:
                recent_hours = [(ts / 3600) % 24 for ts in timestamps[-20:]]
                night_ratio = sum(1 for h in recent_hours if h < 5 or h > 23) / max(
                    len(recent_hours), 1
                )
                if night_ratio < 0.1:
                    signals.append(
                        f"Transaction at {hour:.0f}:00 -- unusual (only {night_ratio * 100:.0f}% night activity)"
                    )
                    risk_scores.append(40)
        else:
            # New or thin-history card
            if amount > 500:
                signals.append(f"High-value ${amount:.2f} on new/low-history card")
                risk_scores.append(35)

        final_score = (
            min(max(risk_scores) * 0.7 + np.mean(risk_scores) * 0.3, 100)
            if risk_scores
            else 5.0
        )
        confidence = min(0.5 + len(signals) * 0.15, 0.95)

        return AgentAssessment(
            agent_name="Velocity Agent",
            risk_score=round(float(final_score), 1),
            confidence=round(confidence, 2),
            signals=signals,
            explanation=(
                f"Velocity analysis: {'; '.join(signals)}"
                if signals
                else "Velocity analysis: No anomalies detected."
            ),
        )
