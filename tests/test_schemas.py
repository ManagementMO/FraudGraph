"""Tests for Pydantic schemas: Transaction, AgentAssessment, FraudVerdict."""
import pytest
from pydantic import ValidationError


def test_transaction_accepts_all_fields():
    """Transaction model accepts all expected fields."""
    from backend.models.schemas import Transaction

    t = Transaction(
        transaction_id="txn_001",
        amount=150.50,
        card_id="card_123",
        merchant_id="merchant_456",
        device_id="device_789",
        ip_address="192.168.1.1",
        timestamp=1234567.0,
        hour_of_day=14.5,
        product_category="W",
        card_type="visa",
        addr1=300.0,
        addr2=87.0,
        device_type="desktop",
        is_fraud=0,
    )
    assert t.transaction_id == "txn_001"
    assert t.amount == 150.50
    assert t.card_id == "card_123"
    assert t.merchant_id == "merchant_456"
    assert t.device_id == "device_789"
    assert t.ip_address == "192.168.1.1"
    assert t.timestamp == 1234567.0
    assert t.hour_of_day == 14.5
    assert t.product_category == "W"
    assert t.card_type == "visa"
    assert t.addr1 == 300.0
    assert t.addr2 == 87.0
    assert t.device_type == "desktop"
    assert t.is_fraud == 0


def test_transaction_optional_defaults():
    """Transaction model works with only required fields."""
    from backend.models.schemas import Transaction

    t = Transaction(transaction_id="txn_002", amount=50.0, card_id="card_001")
    assert t.merchant_id is None
    assert t.device_id is None
    assert t.ip_address is None
    assert t.timestamp == 0.0
    assert t.hour_of_day == 12.0
    assert t.product_category is None
    assert t.card_type is None
    assert t.addr1 is None
    assert t.addr2 is None
    assert t.device_type is None
    assert t.is_fraud is None


def test_agent_assessment_model():
    """AgentAssessment model has correct fields."""
    from backend.models.schemas import AgentAssessment

    a = AgentAssessment(
        agent_name="velocity",
        risk_score=75.0,
        confidence=0.85,
        signals=["high_amount", "night_transaction"],
        explanation="Elevated risk due to amount spike",
    )
    assert a.agent_name == "velocity"
    assert a.risk_score == 75.0
    assert a.confidence == 0.85
    assert a.signals == ["high_amount", "night_transaction"]
    assert a.explanation == "Elevated risk due to amount spike"


def test_fraud_verdict_model():
    """FraudVerdict model has correct fields and accepts AgentAssessments."""
    from backend.models.schemas import AgentAssessment, FraudVerdict

    assessment = AgentAssessment(
        agent_name="test_agent",
        risk_score=50.0,
        confidence=0.8,
        signals=["signal_1"],
        explanation="Test explanation",
    )
    v = FraudVerdict(
        transaction_id="txn_003",
        final_score=55.0,
        verdict="FLAG",
        agent_assessments=[assessment],
        explanation="Synthesized explanation",
        processing_time_ms=123.45,
    )
    assert v.transaction_id == "txn_003"
    assert v.final_score == 55.0
    assert v.verdict == "FLAG"
    assert len(v.agent_assessments) == 1
    assert v.agent_assessments[0].agent_name == "test_agent"
    assert v.explanation == "Synthesized explanation"
    assert v.processing_time_ms == 123.45


def test_fraud_verdict_accepts_valid_verdicts():
    """FraudVerdict.verdict accepts APPROVE, FLAG, and BLOCK."""
    from backend.models.schemas import AgentAssessment, FraudVerdict

    assessment = AgentAssessment(
        agent_name="test",
        risk_score=50.0,
        confidence=0.8,
        signals=["s1"],
        explanation="e",
    )
    for verdict_str in ["APPROVE", "FLAG", "BLOCK"]:
        v = FraudVerdict(
            transaction_id="t1",
            final_score=50.0,
            verdict=verdict_str,
            agent_assessments=[assessment],
            explanation="e",
            processing_time_ms=10.0,
        )
        assert v.verdict == verdict_str
