---
phase: 03-frontend-dashboard
plan: 01
subsystem: ui
tags: [next.js, react-19, typescript, tailwind-v4, d3, websocket, theming]

# Dependency graph
requires:
  - phase: 02-api-layer
    provides: REST endpoints (/stats, /graph, /analyze, /sample-transactions) and WebSocket /ws/stream
provides:
  - TypeScript interfaces mirroring all backend Pydantic models
  - API fetch helpers for all 4 REST endpoints plus WS_URL constant
  - Custom useWebSocket hook with connect/send/disconnect/onMessageRef
  - useStats hook for dashboard metrics
  - ThemeProvider with dark/light/cyberpunk themes and localStorage persistence
  - Header component with theme toggle
  - Two-column dashboard layout skeleton with all component import slots
  - 5 stub components with correct prop interfaces for Plans 02 and 03
  - CSS variable theming system with 10 semantic tokens across 3 themes
affects: [03-02, 03-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [css-first-theming-tailwind-v4, data-theme-attribute, useRef-onMessageRef-websocket, d3-simulationnodedatum-extension]

key-files:
  created:
    - frontend/src/lib/types.ts
    - frontend/src/lib/api.ts
    - frontend/src/hooks/useWebSocket.ts
    - frontend/src/hooks/useStats.ts
    - frontend/src/components/ThemeProvider.tsx
    - frontend/src/components/Header.tsx
    - frontend/src/components/VerdictBanner.tsx
    - frontend/src/components/JudgeTestForm.tsx
    - frontend/src/components/AgentReasoningPanel.tsx
    - frontend/src/components/GraphVisualization.tsx
    - frontend/src/components/StatsBar.tsx
  modified:
    - frontend/src/app/globals.css
    - frontend/src/app/layout.tsx
    - frontend/src/app/page.tsx

key-decisions:
  - "useRef onMessageRef pattern avoids stale closure issues in WebSocket callbacks"
  - "Tailwind v4 CSS-first theming with @custom-variant and @theme inline directives (no tailwind.config.js)"
  - "data-theme='dark' set on html element as SSR default to prevent flash of unstyled content"
  - "Stub components with correct prop types ensure next build passes and Plans 02/03 can replace them"

patterns-established:
  - "CSS variable theming: 10 semantic tokens (bg-primary, bg-secondary, text-primary, text-secondary, accent, border, card-bg, success, warning, danger) per theme"
  - "All interactive components use 'use client' directive"
  - "WebSocket hook uses onMessageRef (useRef) pattern to avoid stale closures"
  - "Page-level state management with hooks in page.tsx, passed down as props"

requirements-completed: [UI-04]

# Metrics
duration: 12min
completed: 2026-03-14
---

# Phase 3 Plan 01: Foundation Layer Summary

**Dashboard foundation with TypeScript types mirroring backend, 3-theme CSS system (dark/light/cyberpunk), custom WebSocket hook, and two-column layout skeleton**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-14T23:59:38Z
- **Completed:** 2026-03-15T00:12:14Z
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments
- All TypeScript interfaces mirror backend Pydantic models exactly (AgentAssessment, FraudVerdict, AnalyzeRequest, GraphNode, GraphLink, DashboardStats, SampleTransaction, WSMessage)
- Tailwind v4 CSS-first theming with 3 themes (dark/light/cyberpunk) using data-theme attribute and 10 semantic CSS variable tokens
- Custom useWebSocket hook with onMessageRef pattern to avoid stale closures
- Two-column dashboard layout (1fr left / 1.5fr right) with Header, VerdictBanner, and 5 stub components with correct prop interfaces
- next build succeeds clean with zero TypeScript errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TypeScript interfaces, constants, and API helpers** - `a17a560` (feat)
2. **Task 2: Create hooks, ThemeProvider, and Header component** - `30ad5a1` (feat)
3. **Task 3: Rewrite globals.css, layout.tsx, and page.tsx with full dashboard skeleton** - `2b2ca06` (feat)

## Files Created/Modified
- `frontend/src/lib/types.ts` - All TypeScript interfaces matching backend schemas, color constants, preset transactions
- `frontend/src/lib/api.ts` - API fetch helpers for /stats, /graph, /sample-transactions, /analyze
- `frontend/src/hooks/useWebSocket.ts` - Custom WebSocket hook with connect/send/disconnect/onMessageRef
- `frontend/src/hooks/useStats.ts` - Hook to fetch /stats on mount with loading/error/refetch
- `frontend/src/components/ThemeProvider.tsx` - React context for 3 themes with localStorage persistence
- `frontend/src/components/Header.tsx` - FraudGraph header with theme toggle buttons
- `frontend/src/components/VerdictBanner.tsx` - Stub with verdict/isAnalyzing props
- `frontend/src/components/JudgeTestForm.tsx` - Stub with onSubmit/isAnalyzing props
- `frontend/src/components/AgentReasoningPanel.tsx` - Stub with assessments/isAnalyzing props
- `frontend/src/components/GraphVisualization.tsx` - Stub with data/assessments props
- `frontend/src/components/StatsBar.tsx` - Stub (no props, fetches own data)
- `frontend/src/app/globals.css` - Tailwind v4 CSS-first theming with 3 data-theme variants
- `frontend/src/app/layout.tsx` - ThemeProvider wrapper, Geist fonts, metadata
- `frontend/src/app/page.tsx` - Two-column grid dashboard layout with WebSocket message handler

## Decisions Made
- Used useRef onMessageRef pattern for WebSocket callbacks to avoid stale closures (recommended by research doc)
- Set data-theme="dark" directly on html element in layout.tsx to prevent flash before hydration
- Created stub components with void expressions to suppress unused prop warnings while maintaining correct type signatures
- Added guard in useWebSocket connect() to prevent duplicate connections if already open

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed useRef requiring initial argument in React 19**
- **Found during:** Task 2 (useWebSocket hook)
- **Issue:** React 19 strict types require useRef to be called with an initial value argument
- **Fix:** Added `undefined` as initial value: `useRef<...>(undefined)`
- **Files modified:** frontend/src/hooks/useWebSocket.ts
- **Verification:** `npx tsc --noEmit` passes clean
- **Committed in:** 30ad5a1 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor type fix required for React 19 compatibility. No scope creep.

## Issues Encountered
None - build passed on first attempt after the useRef fix.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All types, hooks, and theme system ready for Plans 02 and 03 to consume
- 5 stub components with correct prop interfaces ready to be replaced with full implementations
- page.tsx WebSocket flow (handleSubmit, message handler) wired and ready for real components

## Self-Check: PASSED

All 14 files verified present. All 3 task commits verified in git log. Theme system has 5 data-theme references in globals.css (3 selector blocks + 2 custom-variant declarations).

---
*Phase: 03-frontend-dashboard*
*Completed: 2026-03-14*
