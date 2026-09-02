## When to read this file

Read to implement official macro calendars, releases, and surprise calculations. Also read [macro-data.md](../data/macro-data.md).

# Goal

Provide point-in-time macro context and a visible upcoming-event calendar.

# Dependencies

[Phase 2](phase-2-news.md), official Fed/BLS/BEA/FRED/ALFRED access, and persisted market sessions.

# Tasks

- Implement event taxonomy, release schedule, Fed ingestion, BLS series, BEA series, and FRED/ALFRED state features.
- Store scheduled/released timestamps and actual/consensus/previous values.
- Calculate raw and standardized surprises and NQ/yield post-release outcomes.
- Expose calendar/upcoming/event endpoints and dashboard display.

# Acceptance Criteria

Dashboard shows the next important event; released events show actual, consensus, previous, surprise, and point-in-time availability; vintage-aware history is used where available. The current provider layer includes BLS series, the official BLS release calendar, FRED/ALFRED, and BEA normalized observations. Explicit release linking and raw surprise persistence are covered by the current service tests.

# Tests

Parsing, surprise math, vintage selection, release timing, event categorization, and API integration tests. The initial BLS adapter and timestamp-separation behavior are covered in `apps/api/tests/test_macro.py`.

# Explicitly Out of Scope

Bias engine, ML, deep learning, graph, and execution.

# Next Phase

[Phase 4 — Bias engine](phase-4-bias-engine.md).
