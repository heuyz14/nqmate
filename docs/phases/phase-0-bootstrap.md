## When to read this file

Read when implementing the initial repository and service skeleton. Also read [ARCHITECTURE.md](../ARCHITECTURE.md), [endpoints.md](../api/endpoints.md), and [CURRENT_STATE.md](../CURRENT_STATE.md).

# Goal

Create a runnable monorepo foundation for the Next.js frontend and FastAPI backend with validated configuration and database/graph health checks.

# Dependencies

None. Preserve the decisions in [ARCHITECTURE.md](../ARCHITECTURE.md).

# Tasks

- Create `apps/web`, `apps/api`, packages, services, jobs, models, notebooks, and tests structure.
- Configure Next.js/TypeScript/Tailwind and Python 3.12+/FastAPI/Pydantic.
- Add typed environment validation for provider and database secrets without exposing service keys.
- Add Supabase/PostgreSQL and Neo4j connection abstractions, local Docker development, and `GET /health`.

# Acceptance Criteria

Both apps start; `/health` returns 200; database and graph health are visible; no secrets are committed or sent to the browser.

# Tests

Configuration validation tests, API health test, connection abstraction tests, and frontend/backend type/lint checks where configured.

# Explicitly Out of Scope

Market ingestion, features, news, macro, AI bias, Graphiti, ML, and automated trading.

# Next Phase

[Phase 1 — Historical market engine](phase-1-market-engine.md).

