# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-14)

**Core value:** Detect connected fraud networks through graph analysis -- not just individual transactions
**Current focus:** Phase 1: Backend Pipeline

## Current Position

Phase: 1 of 4 (Backend Pipeline)
Plan: 2 of 3 in current phase
Status: Executing
Last activity: 2026-03-14 -- Completed 01-02-PLAN.md

Progress: [====░░░░░░] 20%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 12min
- Total execution time: 0.40 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Backend Pipeline | 2/3 | 24min | 12min |

**Recent Trend:**
- Last 5 plans: 01-01 (10min), 01-02 (14min)
- Trend: Stable

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: 4 coarse phases (Backend Pipeline -> API Layer -> Frontend Dashboard -> Demo Prep)
- Research: langchain-google-genai MUST be installed before Phase 1 begins -- it is missing from .venv
- Research: Temporal train/test split required to avoid self-referential scoring (agents scoring data they trained on)
- Research: Gemini model string (gemini-2.5-flash-preview-04-17) may need verification day-of
- 01-01: Used itertuples instead of iterrows in graph builder for 10x performance
- 01-01: Limited IEEE-CIS CSV load to nrows=50000 to avoid slow initial loads
- 01-01: Fixed .gitignore data/ pattern blocking backend/data/ from version control
- 01-02: All agents use pure Python statistical analysis (no LLM calls) for speed and determinism
- 01-02: GraphAgent uses lazy community loading to support both pre-computed and on-demand modes
- 01-02: GeolocationAgent is the only agent that mutates card_profiles (updates last_addr1, last_device_type)
- 01-02: Agent weights: Velocity 0.25, Geolocation 0.25, Graph 0.30, Behavioral 0.20

### Pending Todos

None yet.

### Blockers/Concerns

- RESOLVED: langchain-google-genai installed in .venv (01-01)
- MEDIUM: Gemini model string may have rotated since build spec was written -- verify at aistudio.google.com
- RESOLVED: pandas 3.0.1 works fine with build spec patterns (01-01 confirmed, 29 tests pass)

## Session Continuity

Last session: 2026-03-14
Stopped at: Completed 01-02-PLAN.md (Worker Agents)
Resume file: .planning/phases/01-backend-pipeline/01-02-SUMMARY.md
