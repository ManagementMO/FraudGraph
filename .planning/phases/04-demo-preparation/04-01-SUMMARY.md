---
phase: 04-demo-preparation
plan: 01
subsystem: demo
tags: [ieee-cis, gemini-cache, demo-narrative, card-discovery, pipeline]

# Dependency graph
requires:
  - phase: 01-backend-pipeline
    provides: FraudDetectionPipeline with agents, graph, card_profiles
  - phase: 02-api-layer
    provides: FastAPI server with lifespan startup and WebSocket streaming
  - phase: 03-frontend-dashboard
    provides: Next.js dashboard with PRESET_TRANSACTIONS and D3 graph
provides:
  - Real IEEE-CIS card_ids for 3-act demo (APPROVE, FLAG, BLOCK)
  - Gemini explanation cache (10 entries) for demo reliability
  - Cache-first explanation lookup in CoordinatorAgent.synthesize()
  - Demo dry-run script validating all 3 acts
  - Server-side cache loading on startup
affects: [04-demo-preparation]

# Tech tracking
tech-stack:
  added: []
  patterns: [cache-first-fallback, data-exploration-scripts, demo-dry-run]

key-files:
  created:
    - backend/demo/__init__.py
    - backend/demo/find_demo_cards.py
    - backend/demo/build_cache.py
    - backend/demo/demo_scenarios.py
    - backend/demo/demo_cards.json
    - backend/demo/gemini_cache.json
  modified:
    - backend/agents/coordinator_agent.py
    - backend/server.py
    - frontend/src/lib/types.ts

key-decisions:
  - "Removed fraud exposure filter from Act 1 card discovery -- nearly all cards have merchant-level exposure in IEEE-CIS data"
  - "Real card_ids: act1=card_1662_visa_debit (APPROVE 12.8), act2=card_13926_discover_credit (FLAG 51.7), act3=card_12695_visa_debit (BLOCK 74.7)"
  - "Cache contains 10 entries: 4 presets + 6 bonus fraud transactions from test set"
  - "Direct _explanation_cache injection in server.py lifespan avoids changing CoordinatorAgent constructor call that tests depend on"

patterns-established:
  - "Cache-first fallback: cache -> live Gemini -> rule-based (3-tier)"
  - "Demo card discovery: data exploration script that runs pipeline to find cards matching target verdicts"

requirements-completed: [DEMO-01, DEMO-03]

# Metrics
duration: 8min
completed: 2026-03-15
---

# Phase 4 Plan 1: Demo Scenarios & Cache Summary

**3-act demo with real IEEE-CIS card_ids (APPROVE 12.8, FLAG 51.7, BLOCK 74.7) and 10-entry Gemini explanation cache with 3-tier fallback**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-15T01:07:58Z
- **Completed:** 2026-03-15T01:16:57Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Discovered real IEEE-CIS card_ids that produce the exact 3-act narrative: APPROVE (12.8), FLAG (51.7), BLOCK (74.7)
- Built Gemini explanation cache with 10 entries (4 presets + 6 bonus fraud transactions)
- Added cache-first explanation lookup to CoordinatorAgent with 3-tier fallback chain
- Created demo dry-run script (demo_scenarios.py) that validates all 3 acts pass
- Updated frontend PRESET_TRANSACTIONS with real card_ids from IEEE-CIS data
- Act 3 fraud ring card (card_12695_visa_debit) has 1096 graph nodes and 762 shared-device cards

## Task Commits

Each task was committed atomically:

1. **Task 1: Find demo card_ids and add cache-first logic** - `7dae16f` (feat)
2. **Task 2: Generate cache, create dry-run, update presets** - `7bccd83` (feat)

## Files Created/Modified
- `backend/demo/__init__.py` - Demo package init
- `backend/demo/find_demo_cards.py` - Data exploration script discovering card_ids for 3-act demo
- `backend/demo/build_cache.py` - Generates Gemini explanation cache JSON
- `backend/demo/demo_scenarios.py` - Dry-run script verifying all 3 acts produce expected verdicts
- `backend/demo/demo_cards.json` - Discovered card_ids: act1, act2, act3, night
- `backend/demo/gemini_cache.json` - 10 cached explanations (4 presets + 6 bonus)
- `backend/agents/coordinator_agent.py` - Added cache-first explanation lookup in synthesize()
- `backend/server.py` - Loads Gemini cache on startup via lifespan
- `frontend/src/lib/types.ts` - PRESET_TRANSACTIONS with real IEEE-CIS card_ids

## Decisions Made
- Removed fraud exposure filter from Act 1 card discovery: nearly all IEEE-CIS cards have non-zero exposure because merchant-level fraud rates are high. The verdict-based check (APPROVE with score < 30) is sufficient.
- Real card_ids discovered by running pipeline against actual IEEE-CIS data (not hardcoded).
- Cache injection uses direct attribute assignment (`pipeline.coordinator._explanation_cache = ...`) in server.py lifespan to avoid changing the CoordinatorAgent constructor signature that 77 existing tests depend on.
- Night transaction reuses act2 card (card_13926_discover_credit) since it produces FLAG at both scenarios.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Act 1 card discovery filter**
- **Found during:** Task 2 (running find_demo_cards.py)
- **Issue:** Act 1 search required exposure_score == 0 but nearly all IEEE-CIS cards have merchant-level fraud exposure, yielding 0 candidates
- **Fix:** Removed exposure filter; rely on verdict == APPROVE and score < 30 as the selection criteria
- **Files modified:** backend/demo/find_demo_cards.py
- **Verification:** Re-ran script, found card_1662_visa_debit with APPROVE score 12.8
- **Committed in:** 7bccd83 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary fix for correct card discovery. No scope creep.

## Issues Encountered
- No Gemini API key available at build time, so cache contains rule-based explanations. The cache can be regenerated with `python -m backend.demo.build_cache` when GOOGLE_API_KEY is set.

## User Setup Required
None - no external service configuration required. Cache works with rule-based fallback.

## Next Phase Readiness
- All 3 demo acts verified (APPROVE, FLAG, BLOCK)
- Cache serves explanations without hitting Gemini API
- Frontend presets use real card_ids that exist in training data
- Ready for 04-02 (final polish, if applicable)

---
*Phase: 04-demo-preparation*
*Completed: 2026-03-15*
