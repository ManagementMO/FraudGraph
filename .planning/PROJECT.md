# FraudGraph

## What This Is

A multi-agent financial fraud detection system that uses graph-based network analysis to detect fraud rings — not just individual suspicious transactions. Four specialized AI agents (velocity, geolocation, graph network, behavioral) independently analyze transactions, then a coordinator agent synthesizes their findings into a final verdict with explainable reasoning. Built for the GenAI Genesis 2026 hackathon (March 13-15, University of Toronto).

## Core Value

Detect connected fraud networks through graph analysis — the thing that sets FraudGraph apart from every other fraud detection tool that only flags individual transactions.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Multi-agent fraud detection pipeline with 4 specialized worker agents + 1 coordinator
- [ ] Transaction graph built with NetworkX showing card-merchant-device relationships
- [ ] Real-time WebSocket streaming of agent reasoning to the frontend
- [ ] Interactive D3.js fraud network graph visualization in the dashboard
- [ ] FastAPI backend serving analysis results and streaming agent deliberation
- [ ] Next.js dashboard with Recharts metrics, risk gauges, and transaction tables
- [ ] IEEE-CIS real dataset loading with synthetic fallback for safety
- [ ] Pydantic data models as the contract between all agents
- [ ] Google Gemini (via langchain-google-genai) as the LLM — NO OpenAI/Anthropic
- [ ] LangGraph multi-agent workflow orchestrating all agents
- [ ] Evaluation metrics proving detection accuracy on real data
- [ ] Demo-ready polished UI that impresses hackathon judges

### Out of Scope

- Mobile app — web-only for hackathon
- User authentication — no login needed for demo
- Database persistence — in-memory for hackathon speed
- Docker/deployment — local demo only
- Real-time production monitoring — this is a demo, not a production system

## Context

- **Hackathon**: GenAI Genesis 2026, March 13-15, University of Toronto. Judged on innovation, technical execution, and demo quality.
- **Solo build**: One person building everything with Claude Code as the coding agent.
- **Dataset**: IEEE-CIS Fraud Detection dataset from Kaggle (~590K transactions, ~3.5% fraud rate) already downloaded in `data/`.
- **Existing state**: Fresh Next.js scaffold in `frontend/`, empty `backend/` directory, real dataset ready.
- **API key**: Google Gemini API key is ready and configured.
- **Two detailed spec documents** in `planning/` — the Build Spec has exact code for every component, the Implementation Guide has hour-by-hour timeline and architecture details.

## Constraints

- **LLM**: Google Gemini only (via langchain-google-genai) — hackathon sponsor requirement, NO OpenAI/Anthropic
- **Timeline**: Must be demo-ready by March 15 afternoon
- **Stack**: Python 3.11+ backend, Next.js + TypeScript + Tailwind frontend — as specified in build docs
- **API Rate Limits**: Gemini free tier — 15 RPM on Flash, 2 RPM on Pro. Design for Flash.
- **Solo**: No team splitting — Claude Code builds everything sequentially

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Google Gemini Flash as primary LLM | Free tier, fast, supports tool calling, hackathon sponsor | -- Pending |
| NetworkX for graph analysis | Well-documented, fast for hackathon-scale data, Python-native | -- Pending |
| LangGraph for multi-agent orchestration | Purpose-built for agent workflows, integrates with LangChain ecosystem | -- Pending |
| D3.js for graph visualization | Industry standard for interactive network graphs, impressive demos | -- Pending |
| Real IEEE-CIS dataset for demo | More impressive to judges than synthetic data, proves real-world capability | -- Pending |
| FastAPI + WebSocket for streaming | Real-time agent reasoning display is a key demo differentiator | -- Pending |

---
*Last updated: 2026-03-14 after initialization*
