"""
Geolocation Agent: Detects location-based anomalies.

Analyzes:
- Impossible travel (addr1 distance * 10km, speed >800km/h = 85, >200km/h = 50)
- Address mismatch (addr1 - addr2 > 200 = 30 score)
- Device type change (different from last_device_type = 25 score)

NOTE: This is the only agent that mutates card_profiles
(updates last_addr1 and last_device_type after analysis).
"""
import math
from backend.models.schemas import AgentAssessment


class GeolocationAgent:
    """
    Detects location-based anomalies:
    - Impossible travel (too far in too little time)
    - Address mismatches
    - Device type changes
    """

    def __init__(self, card_profiles: dict):
        self.card_profiles = card_profiles

    def analyze(self, transaction: dict) -> AgentAssessment:
        card_id = transaction.get("card_id", "unknown")
        addr1 = transaction.get("addr1")
        addr2 = transaction.get("addr2")
        device_type = transaction.get("device_type", "unknown")
        timestamp = float(
            transaction.get("timestamp", transaction.get("TransactionDT", 0))
        )

        signals = []
        risk_scores = []
        profile = self.card_profiles.get(card_id, {})

        # 1. Impossible travel detection
        if (
            profile.get("timestamps")
            and len(profile["timestamps"]) > 0
            and timestamp > 0
        ):
            last_ts = profile["timestamps"][-1]
            time_diff_hours = (timestamp - last_ts) / 3600
            last_addr = profile.get("last_addr1")

            if last_addr is not None and addr1 is not None:
                try:
                    a1, la = float(addr1), float(last_addr)
                    if not (math.isnan(a1) or math.isnan(la)):
                        distance_approx_km = abs(a1 - la) * 10
                        if 0 < time_diff_hours < 2 and distance_approx_km > 500:
                            speed = distance_approx_km / max(time_diff_hours, 0.01)
                            if speed > 800:
                                signals.append(
                                    f"Impossible travel: ~{distance_approx_km:.0f}km in "
                                    f"{time_diff_hours * 60:.0f}min ({speed:.0f} km/h)"
                                )
                                risk_scores.append(85)
                            elif speed > 200:
                                signals.append(
                                    f"Rapid location change: ~{distance_approx_km:.0f}km in "
                                    f"{time_diff_hours * 60:.0f}min"
                                )
                                risk_scores.append(50)
                except (ValueError, TypeError):
                    pass

        # 2. Address mismatch
        if addr1 is not None and addr2 is not None:
            try:
                a1, a2 = float(addr1), float(addr2)
                if not (math.isnan(a1) or math.isnan(a2)) and abs(a1 - a2) > 200:
                    signals.append(
                        f"Large address discrepancy: addr1={int(a1)}, addr2={int(a2)}"
                    )
                    risk_scores.append(30)
            except (ValueError, TypeError):
                pass

        # 3. Device type change
        if profile.get("last_device_type") and device_type not in ("unknown", "None"):
            if device_type != profile["last_device_type"]:
                signals.append(
                    f"Device changed: {profile['last_device_type']} -> {device_type}"
                )
                risk_scores.append(25)

        # Update profile (this agent mutates card_profiles)
        if card_id in self.card_profiles:
            if addr1 is not None:
                try:
                    self.card_profiles[card_id]["last_addr1"] = float(addr1)
                except (ValueError, TypeError):
                    pass
            if device_type not in ("unknown", "None"):
                self.card_profiles[card_id]["last_device_type"] = device_type

        final_score = (
            min(
                max(risk_scores) * 0.7 + sum(risk_scores) / len(risk_scores) * 0.3,
                100,
            )
            if risk_scores
            else 3.0
        )
        confidence = min(0.4 + len(signals) * 0.2, 0.9)

        return AgentAssessment(
            agent_name="Geolocation Agent",
            risk_score=round(float(final_score), 1),
            confidence=round(confidence, 2),
            signals=signals,
            explanation=(
                f"Geolocation analysis: {'; '.join(signals)}"
                if signals
                else "Geolocation analysis: No location anomalies."
            ),
        )
