# OrgBrain — Execution Intelligence Platform
 ab
AI-powered organizational execution intelligence: deterministic simulation and risk
detection first, LLM explains the results second (never computes them).

## Status: Milestone 2 — Backend + Frontend, both verified end-to-end

This is being built incrementally against `01_Vision_Document`, `02_PRD`,
`03_Architecture_Decision_Records`, and `04_SRS_IEEE29148` — see **Progress**
below for exactly what's implemented vs. what's next.

## Quick start

```bash
docker compose up --build
```

This will:
1. Start Postgres + Redis
2. Run Alembic migrations (creates all 12 tables)
3. Seed a synthetic organization (300 employees / 50 projects / 500+ tasks) — skipped on restart if data already exists
4. Start the API at `http://localhost:8000` (docs at `/docs`)
5. Build and start the Next.js dashboard at `http://localhost:3000`

Demo login: `admin@acmedemo.com` / `password123`

## What's implemented

**Backend — fully working, tested against real Postgres:**
- All 12 tables from SRS Appendix B (organizations, users, employees, teams,
  team_memberships, projects, tasks, task_dependencies, risk_events,
  simulation_runs, recommendations, audit_logs) — tenant_id-scoped per ADR-003
- JWT auth + signup/login (`/api/v1/auth/*`)
- Synthetic data generator producing a realistic hierarchy, teams, skills,
  dependency-chained tasks, and intentionally-seeded risk conditions (FR-701)
- **Graph Engine** (NetworkX, ADR-001): org graph builder, hierarchy/cycle detection
- **Simulation Engine**: critical path (DAG longest-path), delay propagation,
  Monte Carlo (triangular distribution resampling, seeded/reproducible),
  capacity violation detection
- **Risk Detection Engine**: execution drift, bottleneck detection (betweenness
  centrality), dependency concentration, capacity violations — all ranked by severity
- **Prediction Engine**: delivery success probability, timeline forecasting, workload imbalance prediction
- **Decision Support Engine**: what-if scenarios (transactional, always rolled back),
  strategic decision validation, resource allocation recommendations
- **Explainability Layer**: Gemini primary / Groq fallback / deterministic offline
  template if no API key configured — LLM only ever explains pre-computed numbers
- 26 REST endpoints, auto-documented via OpenAPI/Swagger at `/docs`
- 15 passing tests (workload, graph, simulation, risk, auth/tenant-isolation) — run with `pytest`

**Frontend — Next.js 14 (App Router) + TypeScript + Tailwind, built and verified
against the live backend:**
- Design: graphite console aesthetic, editorial serif (Fraunces) for headers over
  Inter/IBM Plex Mono for data — two semantic accent colors (signal-amber for risk,
  teal for healthy), not a decorative one
- Auth: login/signup, JWT stored client-side, protected route group with auto-redirect
- **Dashboard** — risk/workload/project KPIs in one view
- **Org Graph** — React Flow rendering of the full 850-node graph (employees/tasks/projects), filterable by type
- **Employees** — workload table, filterable by utilization band
- **Projects** + **Project Detail** — critical path, Monte Carlo trigger, delivery prediction, timeline buffer
- **Risks** — full ranked feed, filterable by risk type
- **Simulation** — what-if scenario runner (add capacity), baseline vs. scenario delta
- **Recommendations** — resource allocation pairs + decision validation with inline LLM explanation
- **AI Assistant** — chat grounded in computed evidence, not free-form guessing
- Production build passes clean (`npm run build`), 12 routes compiled

**Verified live end-to-end**: signup → login → dashboard data → org graph (850
nodes/1947 edges rendered) → project critical path → Monte Carlo simulation →
risk feed → what-if scenario → decision validation with explanation → chat.
Real HTTP requests against the real backend, not mocked.

## What's NOT yet built (next milestones)

- Rate limiting (FR-802)
- CRUD write endpoints for employees/projects/tasks (MVP so far is read + simulate/decide, matching PRD's "read-only dashboard" MVP framing — say the word if you want writes sooner)
- Redis caching of simulation runs (wired in docker-compose but unused by the app yet)
- Audit log writes (table exists, nothing writes to it yet)
- Teams and standalone Tasks pages (data exists via API, just no dedicated frontend page yet)
- Settings page

## Architecture

```
backend/
  app/
    models/        SQLAlchemy models (1:1 with SRS Appendix B)
    schemas/        Pydantic request/response schemas
    api/v1/         FastAPI routers (auth, entities, graph, simulation, risks, decisions)
    services/        graph_service, workload_service, simulation_service,
                      risk_service, prediction_service, decision_service,
                      explainability_service — all the deterministic logic
    core/            security.py (JWT/bcrypt), tenancy.py (auth dependency)
    synthetic/       generator.py + seed.py
  alembic/           real migration, autogenerated + applied against live Postgres
  tests/             pytest, 15 tests, all passing against real Postgres

frontend/
  src/
    app/
      login/                     public
      (protected)/               wrapped in AppShell, auth-gated
        dashboard/ graph/ employees/ projects/ projects/[id]/
        risks/ simulation/ recommendations/ assistant/
    components/       app-shell.tsx (nav), ui.tsx (Card/Badge/Stat/etc.)
    lib/               api.ts (typed client), auth-context.tsx, utils.ts

docker-compose.yml     postgres + redis + backend + frontend, one command up
```
## Next milestone

Writes (task/project updates), audit logging, Redis-backed simulation caching,
rate limiting, Teams/Tasks/Settings pages.

