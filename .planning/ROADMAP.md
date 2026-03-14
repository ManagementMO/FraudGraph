# Roadmap: FraudGraph

## Overview

FraudGraph goes from raw IEEE-CIS data to a demo-ready multi-agent fraud detection system in 4 phases. Phase 1 builds the entire backend pipeline (data loading, graph construction, all 5 agents with Gemini-powered explanations). Phase 2 wires it up through FastAPI REST and WebSocket endpoints. Phase 3 constructs the Next.js dashboard with D3.js graph visualization and real-time agent reasoning. Phase 4 locks in demo reliability with pre-identified fraud rings, evaluation metrics, and Gemini response caching.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Backend Pipeline** - Data loading, graph construction, all 5 agents, and Gemini-powered explanations
- [ ] **Phase 2: API Layer** - FastAPI REST endpoints and WebSocket streaming connecting agents to frontend
- [ ] **Phase 3: Frontend Dashboard** - Next.js dashboard with D3.js graph, agent reasoning panel, and judge interaction
- [ ] **Phase 4: Demo Preparation** - Fraud ring scenarios, batch evaluation metrics, and Gemini caching for reliable demo

## Phase Details

### Phase 1: Backend Pipeline
**Goal**: A working fraud detection pipeline that accepts a transaction and returns a complete verdict with explanations from all 5 agents
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, AGNT-01, AGNT-02, AGNT-03, AGNT-04, AGNT-05, AGNT-06
**Success Criteria** (what must be TRUE):
  1. System loads IEEE-CIS dataset with temporal train/test split and falls back to synthetic data if dataset is missing
  2. NetworkX graph exists with card, merchant, and device nodes connected by transaction edges
  3. Each of the 4 worker agents (velocity, geolocation, graph, behavioral) returns a scored assessment for a given transaction
  4. Coordinator agent synthesizes worker assessments into a FraudVerdict with confidence-weighted scoring and a Gemini-generated natural language explanation
  5. Running the pipeline end-to-end on a sample transaction produces a complete FraudVerdict Pydantic object with all fields populated
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md -- Foundation + data pipeline (schemas, loader with temporal split, graph builder)
- [x] 01-02-PLAN.md -- Worker agents (velocity, geolocation, graph, behavioral)
- [x] 01-03-PLAN.md -- Coordinator agent with Gemini + end-to-end pipeline runner

### Phase 2: API Layer
**Goal**: Frontend can call REST endpoints and receive WebSocket streams to analyze transactions and display results
**Depends on**: Phase 1
**Requirements**: API-01, API-02, API-03, API-04, API-05
**Success Criteria** (what must be TRUE):
  1. POST /analyze accepts a transaction payload and returns a full FraudVerdict JSON response
  2. WebSocket /ws/stream sends each agent's assessment as it completes, enabling real-time display
  3. GET /stats returns accurate dashboard metrics (total transactions, fraud rate, graph node/edge counts)
  4. GET /graph/{card_id} returns a subgraph JSON structure suitable for D3.js force-directed rendering
  5. GET /sample-transactions returns a list of sample transactions for the frontend feed
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md -- FastAPI server with REST endpoints (POST /analyze, GET /stats, /graph, /sample-transactions)
- [ ] 02-02-PLAN.md -- WebSocket /ws/stream with agent-by-agent streaming and dramatic timing

### Phase 3: Frontend Dashboard
**Goal**: Judges can interact with a polished dashboard to submit transactions, watch agents reason in real-time, and explore fraud network graphs
**Depends on**: Phase 2
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07
**Success Criteria** (what must be TRUE):
  1. Judge can type custom transaction values into a form and see live agent results stream in within seconds
  2. Agent reasoning panel shows each agent's assessment with score bars and consensus/disagreement visualization
  3. D3.js force-directed graph renders a fraud network with color-coded nodes (card, merchant, device) that is interactive (zoom, drag, hover)
  4. Dashboard displays key metrics (transaction count, fraud rate, graph size) and the final APPROVE/FLAG/BLOCK verdict with color coding and processing time
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Demo Preparation
**Goal**: Demo runs reliably under pressure with pre-scripted fraud ring scenarios, proven accuracy metrics, and no rate limit failures
**Depends on**: Phase 3
**Requirements**: DEMO-01, DEMO-02, DEMO-03
**Success Criteria** (what must be TRUE):
  1. A pre-identified fraud ring scenario is loaded and ready -- running it through the system produces a compelling multi-node graph and high-confidence fraud verdict
  2. Batch evaluation on the test set produces precision, recall, and F1 scores displayed in the UI or available for judge Q&A
  3. Gemini explanations for demo scenarios are cached so the demo works even if the API rate-limits during the presentation
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend Pipeline | 3/3 | Complete    | 2026-03-14 |
| 2. API Layer | 0/2 | Not started | - |
| 3. Frontend Dashboard | 0/3 | Not started | - |
| 4. Demo Preparation | 0/2 | Not started | - |
