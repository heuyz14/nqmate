# Historical Research & Validation V2 implementation plan

Source: [V2 specification](../../NQMATE_Historical_Research_Validation_V2_SPEC.md).
Start with Phase 10. Later phases remain queued; no training or promotion is part
of the dataset build. Each task ends with focused tests and a handoff update.

## Immediate: Historical Research Dataset V2

1. **Canonical-bar quality audit** (implemented locally; live audit pending; no dependencies).
   Add a deterministic, versioned report and a read-only stored-history CLI.
   Accept only complete minute coverage in explicit session windows; report
   duplicates, invalid prices, timestamp errors, and contract mismatches.
   Verify missing interior/end bars, DST, and invalid data with unit tests.
   Files: market quality module, audit job, corresponding tests (4 files).
   Run from the repo root using the configured backend environment:
   `apps/api/.venv/bin/python -m jobs.audit_historical_market --start 2024-09-05 --end 2026-09-04`.
   JSON stdout includes per-session missing timestamps and aggregate counts;
   exit 1 means quarantine or no candidate sessions, exit 0 means coverage passes.
   Quarantine is report-only at this stage; no stored rows are changed.
2. **Isolated NQ/ES backfill** (2025 run complete; remaining two-year coverage pending; depends on 1).
   Extend weekly orchestration to approximately September 2024–September 2026,
   with one rate-limited provider and resumable bounded batches. Persist ES raw
   bars/contracts without writing ES into date-keyed NQ session rows. Audit all
   unfiltered market readers before ES ingestion. Preserve contract transitions
   across batch boundaries. Verify product isolation and resume/roll behavior.
   Split reader filtering and paired orchestration into separate <=5-file slices.
   `get_bars` now defaults to NQ-prefixed symbols; explicit raw-symbol reads
   support ES. Both repositories reject non-NQ session writes. The new
   `jobs/backfill_research_market.py` shares one provider across weekly batches,
   preserves per-product contract state, and resolves the preceding weekday on
   resume to recover rollover transitions. It stores raw minutes only and emits
   weekly JSON reports; incomplete valid raw evidence may be stored but remains
   quarantined for research. Invalid batches cannot overwrite raw bars.
   Run from the configured backend environment at repo root:
   `apps/api/.venv/bin/python -m jobs.backfill_research_market --start 2024-09-09 --end 2026-09-04`.
   Start with a single completed session for live verification. Exit 1 means
   quarantine/no candidates. Capture stdout for durable batch reports. Reruns
   upsert the same raw identities; this does not seal a dataset. Exchange-schedule
   and price-adjustment validation remain task 3 work.
3. **Validated session reconstruction** (depends on 1–2).
   Initial full-minute reconstruction is implemented via
   `--reconstruct-nq-sessions`; January–December 2025 completed with this flag.
   Initial output was 209 NQ sessions and 190 paired dates; the completed
   expiration-day correction recovered four more, yielding 213 NQ sessions and
   194 paired dates. Full-session contract policy now excludes expiry day.
   Use `python -m jobs.report_research_coverage PATH_TO_JSONL` for independent
   date counts and overnight/RTH exclusion breakdowns; repeated attempts do not
   inflate counts. Pass multiple report paths in attempt order to combine original
   and recovery runs. The saved 2025 summary is `var/log/research-coverage-2025.json`.
   The 2026 extension through September 8 is complete after a transient API retry
   recovery; combined coverage evidence is `var/log/research-coverage-through-2026-09-08.json`.
   A report-only CME schedule classification accepts only exact closure/early-close
   patterns; the initial inventory has 107 unexplained product/session quarantines
   and therefore is not yet a certified training dataset.
   Complete NQ sessions are persisted; ES stays raw context. Prior-contract
   prices are excluded from gap inputs. Short-session schedules and broader
   rollover validation remain pending, so quarantine is intentionally strict.
   Use canonical minutes, explicit exchange-session windows and known early
   closes/halts; quarantine missing evidence. Never mix unadjusted contracts in
   prior levels/gaps. Test regular/short sessions and cross-roll boundaries.
   Files: session calculations, ingestion service, quality integration, tests.
4. **Immutable dataset and snapshot persistence** (depends on 3).
   Reuse ML dataset metadata, adding versioned manifests and insert-only snapshot
   records with RLS; preserve source hashes and Git/feature/target/quality versions.
   Same version must reproduce equivalent values or reject conflicts. Verify
   repository behavior and migration constraints. Schema/types precede callers.
5. **Point-in-time market snapshots** (depends on 4).
   Generate 08:30/09:00/09:25/09:30/10:00/12:00 ET snapshots from closed minutes.
   Distinguish market event availability from historical retrieval time explicitly:
   current provider records use ingestion time as availability. Do not silently
   rewrite old availability or imply historical live capture. Prior levels and
   ATR must use only eligible evidence. Test future-bar insertion invariance.
6. **Directional and continuous targets** (depends on 5).
   Reuse existing target contracts for 5/15/30/60/120/240 minutes and close;
   separate future outcomes from snapshot inputs. Require exact eligible prices
   and complete paths; keep missing outcomes missing. Test every horizon.
7. **Excursion and path targets** (depends on 6).
   Add raw/ATR MFE and MAE, versioned barriers, ONH/ONL and PDH/PDL first hits.
   Same-minute dual hits remain ambiguous; neither hit is explicit. Test long/
   short semantics, unavailable ATR, missing minutes, and ties.
8. **Dataset build orchestration and acceptance** (depends on 4–7).
   Persist per-batch quality/quarantine reports; resumable runs cannot mutate
   sealed datasets. Report independent sessions, snapshots and horizon coverage.
   Run a bounded live batch, then the full range; require ~450 valid sessions,
   reproducibility and leakage checks before declaring Milestone A complete.

Checkpoint: focused tests after each slice; full backend suite after integration.
Data absence is a reported limitation, never permission to fabricate candles.

## Remaining phases in dependency order

| Phase | Deliverable and acceptance | Dependencies / verification |
| --- | --- | --- |
| 11 | Point-in-time news, macro vintages and scheduled-event context; future articles/revisions cannot change earlier snapshots | 10 snapshot contract; source-specific leakage tests |
| 12 | Target V2 definitions completed in immediate tasks 6–7 | 10; deterministic path fixtures |
| 16a / 17 | Dataset-linked session grouping, repeated chronological folds, session bootstrap intervals, paired baseline comparisons and configurable evidence gates | Validated 10–12; grouping, reproducibility and split tests |
| 14a | Version all PB definitions and fail-closed evidence requirements | 10–12; definition fixtures |
| 14b | Persist PB state transitions, then historical setup/outcome inventory | 14a; transition and replay tests |
| 13 / 14c | Independent regime dimensions and conditional strategy statistics with sample counts | 14b; grouped metrics tests |
| 15a | Rebuild immutable feature-family datasets and rerun deterministic baselines | Validated dataset + 16a/17; lineage and baseline tests |
| 15b / 16b | Logistic, forest and boosting challengers, ablations, chronological calibration; manual promotion gates | 15a; repeated out-of-sample evaluation |
| 18 | Stored global importance and supported local SHAP explanations | Evaluated models; contribution and evidence consistency tests |
| 19 | Replay stored snapshots with explicit outcome reveal | Immutable snapshots; API leakage and browser flow tests |
| 16c / 17b | Evaluation/strategy/registry UI with intervals, counts, baseline and regime breakdowns | Validated reports; API/UI integration tests |
| 20a | Immutable scheduled forward predictions and idempotent outcome attachment | Snapshot/target contracts; immutability and scheduling tests |
| 20b | Separate forward-only performance dashboard | 20a; historical/forward isolation tests |

Expand each later deliverable into <=5-file implementation slices when it starts.
Milestones B/C/D require the spec's evidence, not just working screens.

## Known implementation constraints

- `market_sessions` is unique by date and contains NQ-named fields. ES must not
  overwrite these rows, and unfiltered bar readers need explicit product scope.
- Existing completeness checks only require nonempty overnight/RTH groups.
- Historical `available_at` currently equals retrieval time. Snapshot semantics
  need a documented, versioned historical reconstruction policy.
- Initial audit uses the existing 18:00–16:00 ET window conservatively. It does
  not certify exchange holidays, early closes, roll adjustment, or provider
  entitlement. Explicit schedule support comes before dataset acceptance.
- Preserve the existing user edit in `docs/ml/targets.md`.
