"""
Demo dry-run script: verifies all 3 acts produce expected verdicts.

Runs without Gemini (use_llm=False) but loads the explanation cache
so cached explanations are served. Validates the 3-act demo narrative.

Usage:
    python -m backend.demo.demo_scenarios
"""
import json
import sys
from pathlib import Path

from backend.pipeline import FraudDetectionPipeline, normalize_transaction


def run_demo():
    """Run the 3-act demo dry-run and verify verdicts."""
    print("=" * 60)
    print("FraudGraph Demo Dry-Run (3-Act Fraud Ring Discovery)")
    print("=" * 60)

    # Load discovered card_ids
    cards_path = Path(__file__).parent / "demo_cards.json"
    if not cards_path.exists():
        print("ERROR: demo_cards.json not found. Run find_demo_cards.py first.")
        sys.exit(1)

    with open(cards_path) as f:
        demo_cards = json.load(f)

    # Initialize pipeline without LLM (dry-run)
    print("\nInitializing pipeline (use_llm=False)...")
    pipeline = FraudDetectionPipeline(data_dir="data", sample_size=15000, use_llm=False)
    pipeline.initialize()

    # Load explanation cache
    cache_path = Path(__file__).parent / "gemini_cache.json"
    if cache_path.exists():
        with open(cache_path) as f:
            pipeline.coordinator._explanation_cache = json.load(f)
        print(f"Loaded {len(pipeline.coordinator._explanation_cache)} cached explanations")
    else:
        print("WARNING: No cache file found. Explanations will be rule-based.")

    results = []

    # ── Act 1: Normal Transaction (APPROVE) ─────────────────────────
    print("\n" + "=" * 60)
    print("ACT 1: The Normal Transaction")
    print("A routine $25.50 grocery purchase during business hours.")
    print("=" * 60)

    txn1 = normalize_transaction({
        "transaction_id": "demo_normal",
        "amount": 25.50,
        "card_id": demo_cards["act1_card"],
        "merchant_id": "merchant_W_300",
        "product_category": "W",
        "hour_of_day": 14.0,
        "timestamp": 0.0,
    })
    verdict1 = pipeline.analyze_transaction(txn1)
    _print_verdict("Act 1", demo_cards["act1_card"], verdict1)

    # Check graph data
    graph1 = pipeline.graph.get_graph_data_for_frontend(demo_cards["act1_card"])
    print(f"  Graph: {len(graph1['nodes'])} nodes, {len(graph1['links'])} links")

    act1_pass = verdict1.verdict == "APPROVE"
    results.append(("Act 1 (APPROVE)", act1_pass, verdict1.verdict, verdict1.final_score))

    # ── Act 2: Suspicious Transaction (FLAG) ────────────────────────
    print("\n" + "=" * 60)
    print("ACT 2: The Suspicious Transaction")
    print("A $5,000 electronics purchase at 3 AM. Something's not right.")
    print("=" * 60)

    txn2 = normalize_transaction({
        "transaction_id": "demo_suspicious",
        "amount": 5000,
        "card_id": demo_cards["act2_card"],
        "merchant_id": "merchant_H_999",
        "product_category": "H",
        "hour_of_day": 3.0,
        "timestamp": 0.0,
    })
    verdict2 = pipeline.analyze_transaction(txn2)
    _print_verdict("Act 2", demo_cards["act2_card"], verdict2)

    graph2 = pipeline.graph.get_graph_data_for_frontend(demo_cards["act2_card"])
    print(f"  Graph: {len(graph2['nodes'])} nodes, {len(graph2['links'])} links")

    # Accept FLAG or BLOCK (not APPROVE)
    act2_pass = verdict2.verdict in ("FLAG", "BLOCK")
    results.append(("Act 2 (FLAG)", act2_pass, verdict2.verdict, verdict2.final_score))

    # ── Act 3: Fraud Ring (BLOCK) ───────────────────────────────────
    print("\n" + "=" * 60)
    print("ACT 3: The Fraud Ring Discovery")
    print("A $1,200 purchase from a card linked to a massive fraud network.")
    print("=" * 60)

    txn3 = normalize_transaction({
        "transaction_id": "demo_fraud_ring",
        "amount": 1200,
        "card_id": demo_cards["act3_card"],
        "product_category": "W",
        "hour_of_day": 22.0,
        "timestamp": 0.0,
    })
    verdict3 = pipeline.analyze_transaction(txn3)
    _print_verdict("Act 3", demo_cards["act3_card"], verdict3)

    graph3 = pipeline.graph.get_graph_data_for_frontend(demo_cards["act3_card"])
    print(f"  Graph: {len(graph3['nodes'])} nodes, {len(graph3['links'])} links")

    # Accept FLAG or BLOCK with meaningful graph
    act3_pass = verdict3.verdict in ("FLAG", "BLOCK") and len(graph3["nodes"]) > 3
    results.append(("Act 3 (BLOCK)", act3_pass, verdict3.verdict, verdict3.final_score))

    # ── Summary ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("DEMO VERIFICATION RESULTS")
    print("=" * 60)

    all_pass = True
    for name, passed, verdict, score in results:
        status = "PASS" if passed else "FAIL"
        symbol = "[+]" if passed else "[-]"
        print(f"  {symbol} {name}: {status} (got {verdict} at {score})")
        if not passed:
            all_pass = False

    print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")

    if not all_pass:
        print("\nDemo verification FAILED. Check card selection or thresholds.")
        sys.exit(1)
    else:
        print("\nDemo is ready for presentation!")
        sys.exit(0)


def _print_verdict(act_name: str, card_id: str, verdict) -> None:
    """Print a formatted verdict for a demo act."""
    print(f"\n  Card: {card_id}")
    print(f"  Verdict: {verdict.verdict} (score: {verdict.final_score})")
    print(f"  Processing: {verdict.processing_time_ms:.1f}ms")
    print(f"\n  Agent Scores:")
    for a in verdict.agent_assessments:
        top_signal = a.signals[0] if a.signals else "None"
        print(f"    {a.agent_name}: {a.risk_score}/100 (conf: {a.confidence:.2f}) -- {top_signal}")
    print(f"\n  Explanation:")
    for line in verdict.explanation.split("\n"):
        print(f"    {line}")


if __name__ == "__main__":
    run_demo()
