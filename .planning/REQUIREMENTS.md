# Requirements: FraudGraph

**Defined:** 2026-03-14
**Core Value:** Detect connected fraud networks through graph analysis — not just individual transactions

## v1 Requirements

### Data Pipeline

- [x] **DATA-01**: System loads IEEE-CIS dataset (~590K transactions) with synthetic fallback
- [x] **DATA-02**: System builds NetworkX transaction graph with card/merchant/device nodes
- [x] **DATA-03**: System computes card spending profiles from historical data
- [x] **DATA-04**: System uses temporal train/test split to avoid self-referential scoring

### Agents

- [x] **AGNT-01**: Velocity Agent detects rapid transaction patterns (z-score based)
- [x] **AGNT-02**: Geolocation Agent analyzes geographic anomalies (address distance)
- [x] **AGNT-03**: Graph Agent detects fraud networks via shared devices and community analysis
- [x] **AGNT-04**: Behavioral Agent detects deviations from normal spending patterns
- [ ] **AGNT-05**: Coordinator Agent synthesizes assessments with confidence-weighted scoring
- [ ] **AGNT-06**: Coordinator generates LLM-powered explanations via Gemini with rule-based fallback

### API

- [ ] **API-01**: POST /analyze returns full FraudVerdict for a transaction
- [ ] **API-02**: WebSocket /ws/stream streams agent assessments in real-time
- [ ] **API-03**: GET /stats returns dashboard metrics (total txns, fraud rate, graph size)
- [ ] **API-04**: GET /graph/{card_id} returns subgraph for D3 visualization
- [ ] **API-05**: GET /sample-transactions returns sample transactions for the feed

### Frontend

- [ ] **UI-01**: JudgeTestForm lets judges input custom transactions and see live results
- [ ] **UI-02**: AgentReasoningPanel shows each agent's assessment streaming in real-time
- [ ] **UI-03**: D3.js force-directed fraud network graph with color-coded nodes
- [ ] **UI-04**: StatsBar showing key metrics (transaction count, fraud rate, graph nodes)
- [ ] **UI-05**: Agent consensus/disagreement visualization with score bars
- [ ] **UI-06**: APPROVE/FLAG/BLOCK verdict display with color coding
- [ ] **UI-07**: Processing time prominently displayed

### Demo Preparation

- [ ] **DEMO-01**: Pre-identified fraud ring scenario for demo centerpiece
- [ ] **DEMO-02**: Batch evaluation showing precision/recall/F1 on test set
- [ ] **DEMO-03**: Gemini explanation caching to avoid rate limit during demo

## v2 Requirements

### Enhanced Visualization

- **VIZ-01**: Community visualization in D3 with color-coded clusters
- **VIZ-02**: Transaction feed with click-to-analyze
- **VIZ-03**: Dark theme for professional appearance

### Technical Depth

- **TECH-01**: LangGraph StateGraph wrapper for agent orchestration
- **TECH-02**: Historical trend analysis with time series charts

## Out of Scope

| Feature | Reason |
|---------|--------|
| User authentication / login | Zero demo value — judges don't want to create accounts |
| Database persistence | In-memory is faster and simpler for demo with fixed dataset |
| ML model training pipeline | 36 hours insufficient; rule-based heuristics are more explainable |
| Kafka / streaming pipeline | WebSocket streaming achieves same demo effect without infrastructure |
| Mobile / responsive design | Judges view demos on laptops; desktop-only |
| Multiple LLM providers | Gemini-only per hackathon constraint |
| Docker / deployment | Local demo only |
| Alerting / notifications | No one waits for email alerts during a 3-minute demo |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DATA-04 | Phase 1 | Complete |
| AGNT-01 | Phase 1 | Complete |
| AGNT-02 | Phase 1 | Complete |
| AGNT-03 | Phase 1 | Complete |
| AGNT-04 | Phase 1 | Complete |
| AGNT-05 | Phase 1 | Pending |
| AGNT-06 | Phase 1 | Pending |
| API-01 | Phase 2 | Pending |
| API-02 | Phase 2 | Pending |
| API-03 | Phase 2 | Pending |
| API-04 | Phase 2 | Pending |
| API-05 | Phase 2 | Pending |
| UI-01 | Phase 3 | Pending |
| UI-02 | Phase 3 | Pending |
| UI-03 | Phase 3 | Pending |
| UI-04 | Phase 3 | Pending |
| UI-05 | Phase 3 | Pending |
| UI-06 | Phase 3 | Pending |
| UI-07 | Phase 3 | Pending |
| DEMO-01 | Phase 4 | Pending |
| DEMO-02 | Phase 4 | Pending |
| DEMO-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-14*
*Last updated: 2026-03-14 after initial definition*
