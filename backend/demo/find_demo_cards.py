"""
Find real card_ids from IEEE-CIS data for the 3-act demo narrative.

Scans card_profiles to find cards that produce:
  Act 1 (APPROVE): Low-risk normal transaction
  Act 2 (FLAG): Suspicious high-value night transaction
  Act 3 (BLOCK): Card with fraud exposure via shared devices
  Night Transaction: Late-night moderate-value purchase

Usage:
    python -m backend.demo.find_demo_cards
"""
import json
import sys
from pathlib import Path

from backend.pipeline import FraudDetectionPipeline, normalize_transaction


def find_demo_cards():
    """Discover real card_ids for the 3-act demo."""
    print("=" * 60)
    print("FraudGraph Demo Card Discovery")
    print("=" * 60)

    # Initialize pipeline without LLM (no API key needed)
    print("\nInitializing pipeline (use_llm=False)...")
    pipeline = FraudDetectionPipeline(data_dir="data", sample_size=15000, use_llm=False)
    pipeline.initialize()

    card_profiles = pipeline.graph.card_profiles
    print(f"\nTotal card profiles: {len(card_profiles)}")

    results = {}

    # ── Act 1: APPROVE (Normal transaction) ─────────────────────────
    print("\n--- Act 1: Finding APPROVE card ---")
    act1_card = None
    act1_best = None
    act1_best_score = 100

    for card_id, profile in card_profiles.items():
        # Need a card with transaction history but no fraud
        if len(profile["amounts"]) < 3 or profile["fraud_count"] > 0:
            continue

        exposure = pipeline.graph.get_fraud_exposure(card_id)
        if exposure["exposure_score"] > 0:
            continue

        txn = normalize_transaction({
            "transaction_id": "demo_normal",
            "amount": 25.50,
            "card_id": card_id,
            "merchant_id": f"merchant_W_300",
            "product_category": "W",
            "hour_of_day": 14.0,
            "timestamp": 0.0,
        })

        try:
            verdict = pipeline.analyze_transaction(txn)
        except Exception:
            continue

        if verdict.verdict == "APPROVE" and verdict.final_score < 30:
            if verdict.final_score < act1_best_score:
                act1_best_score = verdict.final_score
                act1_best = card_id
                act1_card = {
                    "card_id": card_id,
                    "verdict": verdict.verdict,
                    "score": verdict.final_score,
                }
                if verdict.final_score < 15:
                    break  # Good enough

    if act1_card:
        results["act1_card"] = act1_best
        print(f"  FOUND: {act1_card}")
    else:
        print("  WARNING: No ideal APPROVE card found, will use best candidate")

    # ── Act 2: FLAG (Suspicious transaction) ────────────────────────
    print("\n--- Act 2: Finding FLAG card ---")
    act2_card = None
    act2_best = None
    act2_best_diff = 100  # Distance from target range midpoint (50)

    for card_id, profile in card_profiles.items():
        if len(profile["amounts"]) < 2:
            continue

        txn = normalize_transaction({
            "transaction_id": "demo_suspicious",
            "amount": 5000,
            "card_id": card_id,
            "merchant_id": "merchant_H_999",
            "product_category": "H",
            "hour_of_day": 3.0,
            "timestamp": 0.0,
        })

        try:
            verdict = pipeline.analyze_transaction(txn)
        except Exception:
            continue

        # Ideal: FLAG (30-70), accept anything not APPROVE
        if verdict.verdict == "FLAG":
            diff = abs(verdict.final_score - 50)
            if diff < act2_best_diff:
                act2_best_diff = diff
                act2_best = card_id
                act2_card = {
                    "card_id": card_id,
                    "verdict": verdict.verdict,
                    "score": verdict.final_score,
                }
                if diff < 10:
                    break
        elif verdict.verdict == "BLOCK" and act2_best is None:
            # Accept BLOCK as fallback -- still not APPROVE
            act2_best = card_id
            act2_card = {
                "card_id": card_id,
                "verdict": verdict.verdict,
                "score": verdict.final_score,
            }

    if act2_card:
        results["act2_card"] = act2_best
        print(f"  FOUND: {act2_card}")
    else:
        print("  WARNING: No FLAG/BLOCK card found for Act 2")

    # ── Act 3: BLOCK (Fraud ring card) ──────────────────────────────
    print("\n--- Act 3: Finding BLOCK card (fraud exposure) ---")
    act3_card = None
    act3_best = None
    act3_best_score = 0

    # Find cards with highest fraud exposure
    exposure_candidates = []
    for card_id, profile in card_profiles.items():
        if len(profile["amounts"]) < 1:
            continue
        exposure = pipeline.graph.get_fraud_exposure(card_id)
        if exposure["exposure_score"] >= 25 and exposure["shared_device_cards"] > 0:
            exposure_candidates.append((card_id, exposure))

    # Sort by exposure score descending
    exposure_candidates.sort(key=lambda x: x[1]["exposure_score"], reverse=True)
    print(f"  Candidates with fraud exposure >= 25: {len(exposure_candidates)}")

    for card_id, exposure in exposure_candidates[:50]:
        txn = normalize_transaction({
            "transaction_id": "demo_fraud_ring",
            "amount": 1200,
            "card_id": card_id,
            "product_category": "W",
            "hour_of_day": 22.0,
            "timestamp": 0.0,
        })

        try:
            verdict = pipeline.analyze_transaction(txn)
        except Exception:
            continue

        if verdict.final_score > act3_best_score:
            act3_best_score = verdict.final_score
            act3_best = card_id
            act3_card = {
                "card_id": card_id,
                "verdict": verdict.verdict,
                "score": verdict.final_score,
                "exposure": exposure,
            }

            # Check graph has enough nodes for D3 visualization
            graph_data = pipeline.graph.get_graph_data_for_frontend(card_id)
            act3_card["graph_nodes"] = len(graph_data["nodes"])

            if verdict.verdict == "BLOCK":
                break  # Perfect

    if act3_card:
        results["act3_card"] = act3_best
        print(f"  FOUND: {act3_card}")
    else:
        # Fallback: use highest-scoring card regardless of exposure
        print("  WARNING: No high-exposure BLOCK card found, trying highest-score approach")
        for card_id, profile in card_profiles.items():
            if profile["fraud_count"] > 0:
                txn = normalize_transaction({
                    "transaction_id": "demo_fraud_ring",
                    "amount": 1200,
                    "card_id": card_id,
                    "product_category": "W",
                    "hour_of_day": 22.0,
                    "timestamp": 0.0,
                })
                try:
                    verdict = pipeline.analyze_transaction(txn)
                except Exception:
                    continue
                if verdict.final_score > act3_best_score:
                    act3_best_score = verdict.final_score
                    act3_best = card_id
                    results["act3_card"] = act3_best
                    graph_data = pipeline.graph.get_graph_data_for_frontend(card_id)
                    act3_card = {
                        "card_id": card_id,
                        "verdict": verdict.verdict,
                        "score": verdict.final_score,
                        "graph_nodes": len(graph_data["nodes"]),
                    }
                    if verdict.verdict in ("BLOCK", "FLAG"):
                        break
        if act3_card:
            print(f"  FALLBACK: {act3_card}")

    # ── Night Transaction ───────────────────────────────────────────
    print("\n--- Night Transaction: Finding late-night card ---")
    night_card = None
    night_best = None
    night_best_score = 0

    for card_id, profile in card_profiles.items():
        if len(profile["amounts"]) < 2:
            continue

        txn = normalize_transaction({
            "transaction_id": "demo_night",
            "amount": 800,
            "card_id": card_id,
            "merchant_id": "merchant_C_500",
            "product_category": "C",
            "hour_of_day": 2.5,
            "timestamp": 0.0,
        })

        try:
            verdict = pipeline.analyze_transaction(txn)
        except Exception:
            continue

        if verdict.verdict in ("FLAG", "BLOCK") and verdict.final_score > night_best_score:
            night_best_score = verdict.final_score
            night_best = card_id
            night_card = {
                "card_id": card_id,
                "verdict": verdict.verdict,
                "score": verdict.final_score,
            }
            if verdict.final_score > 40:
                break

    if night_card:
        results["night_card"] = night_best
        print(f"  FOUND: {night_card}")
    else:
        # Fallback: use act2 card for night as well
        if "act2_card" in results:
            results["night_card"] = results["act2_card"]
            print(f"  FALLBACK: Using act2 card {results['act2_card']}")

    # ── Summary ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("RESULTS:")
    print(json.dumps(results, indent=2))
    print("=" * 60)

    # Save to JSON for other scripts
    output_path = Path(__file__).parent / "demo_cards.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {output_path}")

    return results


if __name__ == "__main__":
    find_demo_cards()
