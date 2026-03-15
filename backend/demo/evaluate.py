"""
Batch evaluation script for FraudGraph pipeline.

Runs N test transactions through the pipeline and computes precision, recall,
and F1 metrics at the FLAG threshold. Also identifies graph-specific highlights
where the Graph Agent uniquely detected fraud that other agents missed.

Usage:
    python -m backend.demo.evaluate
"""
import time

from sklearn.metrics import classification_report, f1_score, precision_score, recall_score

from backend.agents.coordinator_agent import CoordinatorAgent

FLAG_THRESHOLD = CoordinatorAgent.THRESHOLDS["FLAG"]


def run_evaluation(pipeline, n: int = 500) -> dict:
    """
    Evaluate the pipeline on the first n rows of test_df.

    Args:
        pipeline: An initialized FraudDetectionPipeline.
        n: Number of test transactions to evaluate.

    Returns:
        Dict with precision, recall, f1, total, fraud_count, flagged_count,
        report (classification_report string), and graph_highlights list.
    """
    test_df = pipeline.test_df
    n = min(n, len(test_df))

    ground_truth = []
    predictions = []
    transaction_details = []

    for row in test_df.head(n).itertuples(index=False):
        txn = row._asdict()
        is_fraud = int(txn.get("isFraud", 0))
        ground_truth.append(is_fraud)

        verdict = pipeline.analyze_transaction(txn)
        predicted = 1 if verdict.final_score >= FLAG_THRESHOLD else 0
        predictions.append(predicted)

        # Track per-agent scores for graph highlights
        graph_score = 0.0
        other_max_score = 0.0
        for assessment in verdict.agent_assessments:
            if assessment.agent_name == "Graph Agent":
                graph_score = assessment.risk_score
            else:
                other_max_score = max(other_max_score, assessment.risk_score)

        transaction_details.append({
            "transaction_id": verdict.transaction_id,
            "graph_score": graph_score,
            "other_max_score": other_max_score,
            "verdict": verdict.verdict,
            "is_fraud": is_fraud,
            "final_score": verdict.final_score,
        })

    # Compute metrics
    precision = precision_score(ground_truth, predictions, zero_division=0)
    recall = recall_score(ground_truth, predictions, zero_division=0)
    f1 = f1_score(ground_truth, predictions, zero_division=0)
    report = classification_report(
        ground_truth, predictions,
        target_names=["Legit", "Fraud"],
        zero_division=0,
    )

    # Identify graph-specific highlights: Graph Agent scored > FLAG_THRESHOLD
    # while all other agents scored below it -- meaning the graph uniquely caught it.
    graph_highlights = [
        {
            "transaction_id": d["transaction_id"],
            "graph_score": d["graph_score"],
            "other_max_score": d["other_max_score"],
            "verdict": d["verdict"],
            "is_fraud": d["is_fraud"],
        }
        for d in transaction_details
        if d["graph_score"] > FLAG_THRESHOLD and d["other_max_score"] < FLAG_THRESHOLD
    ][:5]  # Cap at 5 highlights

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "total": len(predictions),
        "fraud_count": sum(ground_truth),
        "flagged_count": sum(predictions),
        "report": report,
        "graph_highlights": graph_highlights,
    }


def print_results(results: dict) -> None:
    """Print a formatted evaluation summary to stdout."""
    total = results["total"]
    fraud_count = results["fraud_count"]
    fraud_pct = (fraud_count / total * 100) if total > 0 else 0.0

    print()
    print("=" * 55)
    print("  FraudGraph Batch Evaluation")
    print("=" * 55)
    print(f"  Transactions evaluated: {total}")
    print(f"  Fraud in test set:      {fraud_count} ({fraud_pct:.1f}%)")
    print(f"  Flagged by system:      {results['flagged_count']}")
    print()
    print(f"  Precision: {results['precision']:.3f}")
    print(f"  Recall:    {results['recall']:.3f}")
    print(f"  F1 Score:  {results['f1']:.3f}")
    print()
    print(results["report"])

    highlights = results["graph_highlights"]
    print("=" * 55)
    print("  Graph Agent Highlights")
    print("  Cases where Graph Agent caught fraud others missed:")
    print("=" * 55)

    if not highlights:
        print("  (No graph-unique catches in this evaluation run)")
    else:
        for h in highlights:
            fraud_label = "FRAUD" if h["is_fraud"] else "LEGIT"
            print(
                f"  {h['transaction_id']:>12s}  "
                f"Graph: {h['graph_score']:5.1f}  "
                f"Others max: {h['other_max_score']:5.1f}  "
                f"Verdict: {h['verdict']:<7s}  "
                f"Truth: {fraud_label}"
            )
    print()


if __name__ == "__main__":
    from backend.pipeline import FraudDetectionPipeline

    print("Initializing pipeline (use_llm=False, sample_size=15000)...")
    start = time.time()

    pipeline = FraudDetectionPipeline(data_dir="data", sample_size=15000, use_llm=False)
    pipeline.initialize()

    init_time = time.time() - start
    print(f"Pipeline initialized in {init_time:.1f}s")

    print("\nRunning evaluation on 500 test transactions...")
    eval_start = time.time()

    results = run_evaluation(pipeline, n=500)

    eval_time = time.time() - eval_start
    print(f"Evaluation completed in {eval_time:.1f}s")

    print_results(results)

    total_time = time.time() - start
    print(f"Total elapsed: {total_time:.1f}s")
