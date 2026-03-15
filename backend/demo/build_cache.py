"""
Build Gemini explanation cache for demo reliability.

Runs demo transactions through the pipeline with use_llm=True to generate
rich Gemini explanations, then caches them as JSON. Falls back to rule-based
explanations if no Gemini API key is available.

Usage:
    python -m backend.demo.build_cache
"""
import json
import time
from pathlib import Path

from backend.pipeline import FraudDetectionPipeline, normalize_transaction


def build_cache():
    """Generate Gemini explanation cache for demo transactions."""
    print("=" * 60)
    print("FraudGraph Gemini Cache Builder")
    print("=" * 60)

    # Load discovered card_ids
    cards_path = Path(__file__).parent / "demo_cards.json"
    if not cards_path.exists():
        print("ERROR: demo_cards.json not found. Run find_demo_cards.py first.")
        return

    with open(cards_path) as f:
        demo_cards = json.load(f)

    print(f"\nDemo cards: {json.dumps(demo_cards, indent=2)}")

    # Initialize pipeline WITH LLM (will fallback to rule-based if no API key)
    print("\nInitializing pipeline (use_llm=True)...")
    pipeline = FraudDetectionPipeline(data_dir="data", sample_size=15000, use_llm=True)
    pipeline.initialize()

    has_llm = pipeline.coordinator.use_llm and pipeline.coordinator.llm is not None
    if has_llm:
        print("Gemini API available -- will generate LLM explanations")
    else:
        print("WARNING: No Gemini API -- will cache rule-based explanations instead")

    cache = {}

    # Define the 4 preset transactions
    presets = [
        {
            "transaction_id": "demo_normal",
            "amount": 25.50,
            "card_id": demo_cards["act1_card"],
            "merchant_id": "merchant_W_300",
            "product_category": "W",
            "hour_of_day": 14.0,
            "timestamp": 0.0,
        },
        {
            "transaction_id": "demo_suspicious",
            "amount": 5000,
            "card_id": demo_cards["act2_card"],
            "merchant_id": "merchant_H_999",
            "product_category": "H",
            "hour_of_day": 3.0,
            "timestamp": 0.0,
        },
        {
            "transaction_id": "demo_fraud_ring",
            "amount": 1200,
            "card_id": demo_cards["act3_card"],
            "product_category": "W",
            "hour_of_day": 22.0,
            "timestamp": 0.0,
        },
        {
            "transaction_id": "demo_night",
            "amount": 800,
            "card_id": demo_cards["night_card"],
            "merchant_id": "merchant_C_500",
            "product_category": "C",
            "hour_of_day": 2.5,
            "timestamp": 0.0,
        },
    ]

    # Process each preset
    print("\n--- Caching preset transactions ---")
    for i, txn_data in enumerate(presets):
        txn = normalize_transaction(txn_data)
        txn_id = txn["transaction_id"]
        print(f"\n  [{i+1}/{len(presets)}] {txn_id} (card: {txn_data['card_id']})")

        verdict = pipeline.analyze_transaction(txn)
        cache[txn_id] = verdict.explanation
        print(f"    Verdict: {verdict.verdict} ({verdict.final_score})")
        print(f"    Explanation: {verdict.explanation[:100]}...")

        # Rate limit: wait between Gemini calls
        if has_llm and i < len(presets) - 1:
            print("    Waiting 7s for rate limit...")
            time.sleep(7)

    # Also cache some bonus transactions from the test set with isFraud==1
    print("\n--- Caching bonus fraud transactions ---")
    fraud_test = pipeline.test_df[pipeline.test_df["isFraud"] == 1]
    bonus_count = 0
    for _, row in fraud_test.head(10).iterrows():
        txn = normalize_transaction(row.to_dict())
        txn_id = txn["transaction_id"]

        try:
            verdict = pipeline.analyze_transaction(txn)
            cache[txn_id] = verdict.explanation
            bonus_count += 1
            print(f"  Cached {txn_id}: {verdict.verdict} ({verdict.final_score})")

            if has_llm:
                time.sleep(7)

            if bonus_count >= 6:
                break
        except Exception as e:
            print(f"  Skipped {txn_id}: {e}")

    # Save cache
    cache_path = Path(__file__).parent / "gemini_cache.json"
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Cache saved to {cache_path}")
    print(f"Total entries: {len(cache)}")
    print(f"Preset IDs: {[p['transaction_id'] for p in presets]}")
    print(f"Source: {'Gemini LLM' if has_llm else 'Rule-based fallback'}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    build_cache()
