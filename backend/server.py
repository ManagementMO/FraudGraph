"""
FastAPI server for the FraudGraph fraud detection API.

Wraps the FraudDetectionPipeline with REST endpoints for transaction
analysis, dashboard stats, graph visualization, and sample data.
Includes WebSocket streaming for real-time agent-by-agent fraud analysis.

Usage:
    uvicorn backend.server:app --port 8000
"""
import asyncio
import json
import math
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.pipeline import FraudDetectionPipeline, normalize_transaction


# --- Request/Response Models ---


class AnalyzeRequest(BaseModel):
    """POST body for /analyze endpoint."""
    transaction_id: str = "custom_001"
    amount: float = 500.0
    card_id: str = "card_1_visa_debit"
    merchant_id: Optional[str] = "merchant_W_300"
    product_category: Optional[str] = "W"
    hour_of_day: float = 14.0
    timestamp: float = 0.0
    addr1: Optional[float] = None
    addr2: Optional[float] = None
    device_type: Optional[str] = None


# --- Lifespan ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the fraud detection pipeline on startup."""
    start = time.time()
    pipeline = FraudDetectionPipeline(use_llm=True)
    pipeline.initialize()
    # Load Gemini explanation cache for demo reliability
    cache_path = Path(__file__).parent / "demo" / "gemini_cache.json"
    if cache_path.exists():
        with open(cache_path) as f:
            pipeline.coordinator._explanation_cache = json.load(f)
        print(f"Loaded {len(pipeline.coordinator._explanation_cache)} cached explanations")

    app.state.pipeline = pipeline

    elapsed = time.time() - start
    stats = pipeline.get_stats()
    print(
        f"FraudGraph API ready in {elapsed:.1f}s -- "
        f"{stats['train_size']} train txns, "
        f"{stats['node_count']} graph nodes, "
        f"{stats['edge_count']} graph edges"
    )

    yield  # App runs here

    # Shutdown (nothing to clean up)


# --- App ---


app = FastAPI(
    title="FraudGraph API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helpers ---


def sanitize_value(v):
    """Replace NaN/inf float values with None for JSON safety."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def sanitize_dict(d: dict) -> dict:
    """Recursively sanitize a dict, replacing NaN/inf with None."""
    return {k: sanitize_value(v) for k, v in d.items()}


# --- Endpoints ---


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "pipeline_initialized": True}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    """
    Analyze a single transaction for fraud.

    Accepts transaction fields, runs all 4 worker agents + coordinator,
    returns a complete FraudVerdict.
    """
    try:
        pipeline = app.state.pipeline
        txn = normalize_transaction(req.model_dump())
        verdict = pipeline.analyze_transaction(txn)
        return verdict.model_dump()
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/stats")
async def stats():
    """
    Return dashboard metrics from the pipeline.

    Includes node/edge counts, train/test sizes, fraud rates,
    and computed total_transactions / fraud_rate_pct.
    """
    pipeline = app.state.pipeline
    data = pipeline.get_stats()
    # Add computed fields
    data["total_transactions"] = data["train_size"] + data["test_size"]
    if data.get("fraud_rate_train") is not None:
        data["fraud_rate_pct"] = round(data["fraud_rate_train"] * 100, 2)
    else:
        data["fraud_rate_pct"] = None
    return data


@app.get("/graph/{card_id}")
async def graph(
    card_id: str,
    depth: int = Query(default=2, ge=1),
    max_nodes: int = Query(default=50, ge=1),
):
    """
    Return D3-compatible subgraph JSON around a card.

    Returns {nodes: [{id, type, is_fraud, is_target}], links: [{source, target, weight}]}
    with depth and max_nodes capping.
    """
    # Hard caps
    depth = min(depth, 3)
    max_nodes = min(max_nodes, 50)

    pipeline = app.state.pipeline
    data = pipeline.graph.get_graph_data_for_frontend(card_id, depth=depth)

    # Cap nodes if needed
    nodes = data["nodes"]
    if len(nodes) > max_nodes:
        # Prioritize: is_target first, then is_fraud, then others
        nodes.sort(key=lambda n: (n.get("is_target", False), n.get("is_fraud", False)), reverse=True)
        nodes = nodes[:max_nodes]
        kept_ids = {n["id"] for n in nodes}
        data["links"] = [link for link in data["links"] if link["source"] in kept_ids and link["target"] in kept_ids]
        data["nodes"] = nodes

    return data


@app.get("/sample-transactions")
async def sample_transactions(n: int = Query(default=20, ge=1)):
    """
    Return sample transactions from the test set.

    All NaN/inf values are sanitized to None for JSON safety.
    """
    pipeline = app.state.pipeline
    samples = pipeline.get_sample_transactions(n)
    return [sanitize_dict(txn) for txn in samples]


# --- WebSocket ---


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent-by-agent fraud analysis.

    Accepts transaction JSON messages and streams back individual agent
    assessments with dramatic timing (400ms between agents, 800ms before
    verdict) for a compelling demo experience.

    Message types sent:
        - {"type": "agent_assessment", "data": {AgentAssessment fields}}
        - {"type": "final_verdict", "data": {FraudVerdict fields}}
        - {"type": "error", "data": {"message": "..."}}
    """
    await websocket.accept()
    try:
        while True:
            # Receive transaction JSON from client
            raw = await websocket.receive_text()

            try:
                txn = json.loads(raw)
                txn = normalize_transaction(txn)
                txn_id = txn.get("transaction_id", str(txn.get("TransactionID", "unknown")))

                pipeline = app.state.pipeline

                # Run agents individually in LOCKED order for streaming
                agents = [
                    pipeline.velocity_agent,
                    pipeline.geo_agent,
                    pipeline.graph_agent,
                    pipeline.behavioral_agent,
                ]

                assessments = []
                for agent in agents:
                    assessment = agent.analyze(txn)
                    assessments.append(assessment)
                    await websocket.send_json({
                        "type": "agent_assessment",
                        "data": assessment.model_dump(),
                    })
                    await asyncio.sleep(0.4)  # 400ms dramatic delay

                # Pre-verdict pause
                await asyncio.sleep(0.8)  # 800ms before final verdict

                # Coordinator synthesizes final verdict
                verdict = pipeline.coordinator.synthesize(txn_id, assessments)
                await websocket.send_json({
                    "type": "final_verdict",
                    "data": verdict.model_dump(),
                })

            except Exception as e:
                # Error during analysis -- send error but keep connection alive
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Analysis failed: {str(e)}"},
                })

    except WebSocketDisconnect:
        # Normal client disconnect
        pass
    except Exception as e:
        # Unexpected error -- attempt to notify client, then close
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": f"Connection error: {str(e)}"},
            })
        except Exception:
            pass
