"""
Coordinator Agent: Synthesizes all 4 worker agent assessments into a final verdict.

This is the ONLY agent that uses an LLM (Google Gemini via langchain-google-genai).
When Gemini is unavailable or use_llm=False, falls back to rule-based explanations.

Scoring:
- Confidence-weighted average using agent weights:
  Velocity=0.25, Geolocation=0.25, Graph=0.30 (highest), Behavioral=0.20
- Verdict thresholds: APPROVE <30, FLAG 30-70, BLOCK >=70

Explanation format:
- Narrative: 2-3 sentences describing the verdict
- Technical signals: 3-4 bullet points with key risk indicators
"""
import json
import os
import time
from pathlib import Path
from backend.models.schemas import AgentAssessment, FraudVerdict
from dotenv import load_dotenv

load_dotenv()


class CoordinatorAgent:
    """
    Synthesizes all 4 worker agent assessments into a final verdict.
    Uses Google Gemini for human-readable explanations when available.
    """

    WEIGHTS = {
        "Velocity Agent": 0.25,
        "Geolocation Agent": 0.25,
        "Graph Agent": 0.30,      # Highest -- the core differentiator
        "Behavioral Agent": 0.20,
    }

    # User-locked thresholds (NOT build spec values)
    THRESHOLDS = {"BLOCK": 70, "FLAG": 30}

    def __init__(self, use_llm: bool = True, cache_path: str | None = None):
        self.use_llm = use_llm
        self.llm = None

        # Load explanation cache for demo reliability
        self._explanation_cache: dict[str, str] = {}
        if cache_path:
            cp = Path(cache_path)
            if cp.exists():
                with open(cp) as f:
                    self._explanation_cache = json.load(f)
                print(f"CoordinatorAgent: loaded {len(self._explanation_cache)} cached explanations")

        if use_llm:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("WARNING: GOOGLE_API_KEY not set. Falling back to rule-based explanations.")
                self.use_llm = False
            else:
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    self.llm = ChatGoogleGenerativeAI(
                        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                        api_key=api_key,       # v4.x API (NOT google_api_key)
                        temperature=0.3,
                        max_tokens=400,        # v4.x API (NOT max_output_tokens)
                        max_retries=2,
                    )
                except Exception as e:
                    print(f"WARNING: Failed to initialize Gemini: {e}. Using rule-based fallback.")
                    self.use_llm = False

    def synthesize(self, transaction_id: str, assessments: list[AgentAssessment]) -> FraudVerdict:
        """Synthesize agent assessments into a final FraudVerdict."""
        start = time.time()

        # Confidence-weighted score
        weighted_score = 0.0
        total_weight = 0.0
        for a in assessments:
            w = self.WEIGHTS.get(a.agent_name, 0.25) * a.confidence
            weighted_score += a.risk_score * w
            total_weight += w

        final_score = weighted_score / total_weight if total_weight > 0 else 0

        # Verdict using user-locked thresholds
        if final_score >= self.THRESHOLDS["BLOCK"]:
            verdict = "BLOCK"
        elif final_score >= self.THRESHOLDS["FLAG"]:
            verdict = "FLAG"
        else:
            verdict = "APPROVE"

        # Explanation: cache-first for demo reliability, then LLM, then rule-based
        cached_explanation = self._explanation_cache.get(transaction_id)
        if cached_explanation:
            explanation = cached_explanation
        elif self.use_llm and self.llm is not None and final_score > 20:
            explanation = self._llm_explanation(transaction_id, assessments, final_score, verdict)
        else:
            explanation = self._rule_based_explanation(assessments, final_score, verdict)

        return FraudVerdict(
            transaction_id=transaction_id,
            final_score=round(final_score, 1),
            verdict=verdict,
            agent_assessments=assessments,
            explanation=explanation,
            processing_time_ms=round((time.time() - start) * 1000, 3),
        )

    def _llm_explanation(self, txn_id, assessments, score, verdict) -> str:
        """Generate explanation using Gemini LLM."""
        from langchain_core.messages import SystemMessage, HumanMessage

        summaries = "\n".join(
            f"- {a.agent_name}: Risk {a.risk_score}/100 (confidence {a.confidence}). "
            f"Signals: {', '.join(a.signals) if a.signals else 'None'}"
            for a in assessments
        )
        prompt = (
            f"Transaction {txn_id} scored {score:.1f}/100 ({verdict}).\n\n"
            f"Agent assessments:\n{summaries}\n\n"
            f"Write a fraud analysis explanation in this EXACT format:\n"
            f"1. First, write 2-3 sentences as a narrative explaining the verdict. "
            f"Be specific about which signals mattered most.\n"
            f"2. Then list 3-4 bullet points (using - prefix) with key technical signals.\n\n"
            f"Example format:\n"
            f"This transaction is suspicious -- the cardholder typically spends $50 but this "
            f"$2,400 charge came from a previously unseen device at 3AM.\n"
            f"- Velocity z-score: 3.2\n"
            f"- New device detected\n"
            f"- Night-time transaction (3:14 AM)\n\n"
            f"No preamble. Start directly with the narrative."
        )
        try:
            resp = self.llm.invoke([
                SystemMessage(content=(
                    "You are a concise fraud analyst. Write brief, specific explanations. "
                    "Always use the narrative + bullet points format."
                )),
                HumanMessage(content=prompt),
            ])
            return resp.content.strip()
        except Exception as e:
            print(f"Gemini API error: {e}. Falling back to rule-based explanation.")
            return self._rule_based_explanation(assessments, score, verdict)

    def _rule_based_explanation(self, assessments, score, verdict) -> str:
        """Generate explanation using rule-based logic (no LLM needed)."""
        high_risk = [a for a in assessments if a.risk_score > 30]

        if not high_risk:
            return f"Score {score:.1f}/100 ({verdict}). No significant risk signals detected."

        # Sort by risk score descending, take top 2-3
        top_agents = sorted(high_risk, key=lambda x: x.risk_score, reverse=True)[:3]

        # Build narrative from top agents
        narrative_parts = []
        for a in top_agents:
            if a.signals:
                narrative_parts.append(f"{a.agent_name} flagged: {a.signals[0]}")

        narrative = f"Score {score:.1f}/100 ({verdict}). " + ". ".join(narrative_parts) + "." if narrative_parts else f"Score {score:.1f}/100 ({verdict})."

        # Build bullet points from all signals of top agents
        bullets = []
        for a in top_agents:
            for sig in a.signals[:2]:  # Max 2 signals per agent
                bullets.append(f"- {sig}")
                if len(bullets) >= 4:
                    break
            if len(bullets) >= 4:
                break

        if bullets:
            return narrative + "\n" + "\n".join(bullets)
        return narrative
