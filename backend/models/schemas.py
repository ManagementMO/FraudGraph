"""Pydantic models for the FraudGraph fraud detection pipeline."""
from pydantic import BaseModel
from typing import Optional


class Transaction(BaseModel):
    """A single financial transaction to be analyzed."""
    transaction_id: str
    amount: float
    card_id: str
    merchant_id: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: float = 0.0
    hour_of_day: float = 12.0
    product_category: Optional[str] = None
    card_type: Optional[str] = None
    addr1: Optional[float] = None
    addr2: Optional[float] = None
    device_type: Optional[str] = None
    is_fraud: Optional[int] = None  # Ground truth label (for evaluation only)


class AgentAssessment(BaseModel):
    """Output from a single fraud detection agent."""
    agent_name: str
    risk_score: float         # 0-100
    confidence: float         # 0.0-1.0
    signals: list[str]        # List of detected fraud signals
    explanation: str           # Human-readable reasoning


class FraudVerdict(BaseModel):
    """Final synthesized verdict from the Coordinator Agent."""
    transaction_id: str
    final_score: float        # 0-100
    verdict: str              # "APPROVE", "FLAG", or "BLOCK"
    agent_assessments: list[AgentAssessment]
    explanation: str           # Coordinator's synthesized reasoning
    processing_time_ms: float
