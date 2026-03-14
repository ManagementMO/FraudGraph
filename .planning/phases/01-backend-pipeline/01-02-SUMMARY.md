---
phase: 01-backend-pipeline
plan: 02
subsystem: agents
tags: [numpy, networkx, z-score, burst-detection, impossible-travel, community-detection, fraud-exposure, behavioral-analysis]

# Dependency graph
requires:
  - phase: 01-backend-pipeline/01
    provides: "TransactionGraph with card_profiles, AgentAssessment schema, fraud exposure scoring"
provides:
  - "VelocityAgent with z-score amount analysis, 5-min burst detection, and night-time anomaly"
  - "GeolocationAgent with impossible travel, address mismatch, and device change detection"
  - "GraphAgent with fraud network exposure (shared devices), cross-community transactions, and high-degree analysis"
  - "BehavioralAgent with new/rare category detection, amount deviation within category, and new merchant flagging"
  - "20 unit tests covering all 4 agents (normal, anomalous, and edge cases)"
affects: [01-03-PLAN, 02-01]

# Tech tracking
tech-stack:
  added: []
  patterns: [agent-constructor-with-card-profiles, agent-analyze-returns-assessment, dual-key-field-lookup, tdd-red-green]

key-files:
  created:
    - backend/agents/velocity_agent.py
    - backend/agents/geolocation_agent.py
    - backend/agents/graph_agent.py
    - backend/agents/behavioral_agent.py
    - tests/test_agents.py
  modified: []

key-decisions:
  - "All agents use pure Python statistical analysis (no LLM calls) for speed and determinism"
  - "GraphAgent uses lazy community loading (_ensure_communities) to support both pre-computed and on-demand modes"
  - "GeolocationAgent is the only agent that mutates card_profiles (updates last_addr1 and last_device_type)"
  - "Scoring formula: max(risk_scores) * weight + mean(risk_scores) * (1-weight) for balanced signal weighting"

patterns-established:
  - "Agent constructor pattern: __init__(self, card_profiles: dict) or __init__(self, transaction_graph)"
  - "Agent analyze pattern: analyze(self, transaction: dict) -> AgentAssessment"
  - "Dual-key field lookup: transaction.get('amount', transaction.get('TransactionAmt', 0))"
  - "Test fixture pattern: build card_profiles dicts directly without loading data"

requirements-completed: [AGNT-01, AGNT-02, AGNT-03, AGNT-04]

# Metrics
duration: 14min
completed: 2026-03-14
---

# Phase 1 Plan 2: Worker Agents Summary

**4 statistical fraud detection agents (velocity, geolocation, graph, behavioral) with z-score analysis, impossible travel detection, network fraud exposure scoring, and spending pattern deviation**

## Performance

- **Duration:** 14 min
- **Started:** 2026-03-14T21:13:38Z
- **Completed:** 2026-03-14T21:28:20Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- VelocityAgent detects amount spikes (z-score), rapid transaction bursts (5-min window), and night-time anomalies with configurable thresholds
- GeolocationAgent detects impossible travel (addr1 distance >500km in <2h), address mismatches (addr1-addr2 >200), and device type changes -- the only agent that mutates card_profiles
- GraphAgent (highest weight 0.30) detects fraud network exposure through shared devices, cross-community transactions via Louvain, and high-connectivity nodes (>50 connections)
- BehavioralAgent detects new/rare spending categories (Counter-based), amount deviations within category (z-score >2.5), and new merchant patterns -- with thin-history fallback
- All 4 agents return valid AgentAssessment with risk_score 0-100, confidence 0-1, non-empty explanation
- All agents handle unknown/new cards gracefully with low default scores
- 20 agent tests + 29 existing tests = 49 total tests all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Velocity and Geolocation agents with tests** - `6341f91` (feat)
2. **Task 2: Graph and Behavioral agents with tests** - `f7af824` (feat)

## Files Created/Modified
- `backend/agents/velocity_agent.py` - Amount z-score, burst detection, night-time anomaly agent
- `backend/agents/geolocation_agent.py` - Impossible travel, address mismatch, device change agent
- `backend/agents/graph_agent.py` - Fraud network exposure, community analysis, degree analysis agent
- `backend/agents/behavioral_agent.py` - Category deviation, amount deviation, new merchant agent
- `tests/test_agents.py` - 20 unit tests covering all 4 agents

## Decisions Made
- All agents use pure Python statistical analysis (no LLM calls) for speed and determinism, per user decision
- GraphAgent uses lazy community loading to support both pre-computed startup and on-demand computation
- GeolocationAgent is the only agent that mutates card_profiles (updates last_addr1 and last_device_type) to enable impossible travel detection across sequential transactions
- Scoring formulas use weighted max+mean combination: VelocityAgent 0.7/0.3, GraphAgent/BehavioralAgent 0.6/0.4, GeolocationAgent 0.7/0.3

## Deviations from Plan

None - plan executed exactly as written. Test fixture adjustments (night-time timestamps and graph normal card merchant) were part of normal TDD iteration to ensure test correctness.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 worker agents ready for the Coordinator Agent (Plan 01-03)
- VelocityAgent, GeolocationAgent, BehavioralAgent take card_profiles dict from TransactionGraph
- GraphAgent takes TransactionGraph instance directly
- All agents return AgentAssessment compatible with CoordinatorAgent.synthesize()
- Agent weights established: Velocity 0.25, Geolocation 0.25, Graph 0.30, Behavioral 0.20

## Self-Check: PASSED

All 5 files verified present. Both commit hashes (6341f91, f7af824) confirmed in git log. 20/20 agent tests collected. 49/49 total project tests green.

---
*Phase: 01-backend-pipeline*
*Completed: 2026-03-14*
