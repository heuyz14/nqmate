## When to read this file

Always read this file at session start. It is the concise handoff for what exists, what is active, and what should happen next.

# Current State

## Current Phase

Phase 9 — Evaluation (implementation complete; evidence collection continues; no ML model promoted)

## Completed

- Documentation architecture created.
- Phase 0 repository skeleton created.
- Python 3.12 virtual environment and API dependencies installed.
- Next.js dependencies installed and production build verified.
- Git `origin` configured for `git@github.com:heuyz14/nqmate.git`.
- Hosted Supabase and Neo4j AuraDB connectivity verified through the API health endpoint.
- Phase 1 market domain slice: `MarketBar`, `MarketContract`, `MarketSession`, deterministic session calculations, ATR(14), contract selection, Massive response mapping, deduplication, and session API contract.
- Phase 1 persistence slice: Supabase migration and server-side repository payloads for contracts, minute bars, and sessions.
- Session reads now use `SupabaseMarketRepository`; empty dates return HTTP 404 rather than an infrastructure error.
- Contract metadata lookup, bounded backfill command, and chart-ready bars/levels endpoints added.
- One historical NQ session (`2026-08-28`) ingested from Massive into Supabase and verified through the API.
- Contract rollover transition persistence added in migration `002_contract_rollovers.sql`; ingestion records raw-contract changes.
- Backfill is rate-limited to Massive’s five requests per minute; the job reuses contracts until expiration and is safe to resume by date range.
- Phase 1 derived market slice added: `/market/nq/bars` supports `1h`, `4h`, and `1d` deterministic aggregation from stored minute bars; weekly opening-gap calculation is available in the market calculation layer.
- Weekly opening gaps are available through `/api/v1/market/nq/weekly-gaps`.
- Deterministic feature endpoint added at `/api/v1/market/nq/features` with 5m/15m/30m returns, EMA 9/20/50, VWAP, VWAP distance, range position, prior-level distances, and nullable NQ/ES relative strength.
- macOS daily market updater added at `jobs/ingest_market_daily.py`, scheduled by `ops/com.nqmate.market-daily.plist` for 4:05 PM America/New_York.
- Phase 2 news slice added: Marketaux and Fed RSS adapters, strict normalized article/event models, deterministic NQ relevance scoring, and provider/ID deduplication store.
- Phase 2 requirements expanded: Forex Factory calendar, official-release priority, adaptive polling, multi-axis classification, surprise semantics, logical cross-source deduplication, and pre-event risk awareness.
- Phase 2 persistence/API slice added: Supabase migration `003_news.sql`, server-side article/event repository, and `/api/v1/news` plus `/api/v1/news/high-impact` read endpoints.
- Phase 2 calendar/polling slice added: Forex Factory USD calendar normalization, configurable ET adaptive polling cadence, and environment flags for source enablement and relevance thresholds.
- Phase 2 news recency slice added: Marketaux uses publication date filters and API news reads default to a 14-day hot cache while retaining the full Supabase archive.
- Forex Factory CSV export support verified against the configured `nfs.faireconomy.media/ff_calendar_thisweek.csv` feed; date/time values are normalized from the configured `FOREX_FACTORY_TIMEZONE`.
- Phase 2 calendar persistence/API slice added: migration `004_economic_calendar.sql`, stable provider/time event identity, and `/api/v1/macro/calendar` retrieval.
- Phase 2 ingestion slice added: configured Marketaux, Federal Reserve RSS, and Forex Factory providers are orchestrated by `jobs/ingest_news.py`; baseline deterministic article classification is persisted as cached events.
- Phase 2 catalyst-awareness slice added: `/api/v1/macro/upcoming` returns the next HIGH-impact event, minutes until release, pre/post-release risk state, and economic surprise when available; pure surprise/risk logic is tested.
- Phase 2 clustering slice added: normalized news events receive a stable logical-event key for near-duplicate grouping, with canonical-source selection preferring official Fed/BLS/BEA reporting; migration `005_news_clustering.sql` adds the persisted key.
- Phase 2 optional NLP slice added: `GeminiNewsExtractor` is behind `NEWS_NLP_ENABLED`, validates structured output, and is wrapped in a provider/ID cache; deterministic classification remains the default.
- Gemini configuration verified: the key authenticates successfully, the initial retired model was replaced with provider-recommended `gemini-3.6-flash`, and an NLP-enabled ingestion smoke test persisted structured fields successfully.
- Phase 2 completion slice added: clusters persist canonical provider, contributing providers, event count, and availability span; `/api/v1/news/clusters` exposes them, with migration `006_news_event_clusters.sql`.
- Phase 3 foundation slice added: official `BLSProvider` and point-in-time `MacroObservation` preserve release, retrieval, and vintage timestamps without fabricating release availability.
- Phase 3 persistence slice added: migration `007_macro_observations.sql`, `SupabaseMacroRepository`, and `/api/v1/macro/observations` provide bounded official-observation storage and reads.
- Phase 3 official-provider slice added: `FREDProvider` supports FRED/ALFRED realtime vintage bounds, and `BEAProvider` normalizes official dataset observations; both preserve unknown release times.
- Phase 3 release-calendar slice added: `BLSReleaseCalendarProvider` parses the official BLS iCalendar feed into scheduled release records with timezone-aware UTC timestamps; live access remains blocked by BLS/Akamai HTTP 403 on this network.
- BLS calendar parser and mapping are tested; live ingestion currently receives HTTP 403 from BLS/Akamai in this environment, so the source URL is configurable and no fallback data is fabricated.
- Phase 3 observation-ingestion slice added: `jobs/ingest_macro.py --series-id ... --skip-calendar` persists explicit BLS series observations independently of the blocked calendar feed; 2026 CPI smoke test stored 7 observations and API retrieval confirmed their `retrieved_at` metadata.
- Phase 3 release-link/surprise slice added: explicit observation-to-release timestamp linking and `actual - forecast` persistence are implemented; migration `008_macro_surprises.sql` is pending application.
- Migration `008_macro_surprises.sql` applied and verified through the macro API.
- Phase 3 interpretation slice added: deterministic event-specific NQ surprise direction and rationale are persisted with migration `009_macro_surprise_interpretation.sql`.
- Phase 3 reaction-storage slice added: migration `010_macro_reactions.sql`, repository persistence, and event reaction API are implemented for post-release NQ/yield outcome associations.
- Phase 3 reaction-calculation slice added: deterministic point and percentage returns from explicit base/observed prices are tested with zero-base protection.
- Phase 3 market-bar sampling slice added: `sample_reactions` selects eligible pre/post-release NQ minute bars at 5m/15m/30m/60m horizons without imputing missing data.
- Phase 3 event-reaction wiring added: `persist_sampled_reactions` connects sampled labels to calendar event IDs and persists them idempotently.
- Phase 3 provider acceptance smoke tests passed: BLS returned 7 CPI observations, FRED/ALFRED returned observations, BEA returned 25 quarterly observations, and the reaction endpoint returned HTTP 200 against Supabase.
- NQ sessions for 2026-09-01 and 2026-09-02 were successfully retried with contract `NQU6` and verified through the session API.
- Phase 4 deterministic bias slice added: typed `BiasSnapshot`, weighted reproducible scoring, direction thresholds, normalized-input validation, and the 15-minute catalyst guardrail with `WAIT_FOR_RELEASE`.
- Phase 4 evidence slice added: deterministic evidence factors, bull/bear cases, invalidation conditions, and uncertainty notes are included in `BiasResult`.
- Phase 4 API/persistence slice added: migration `011_bias_predictions.sql`, `POST /api/v1/bias/generate`, and `GET /api/v1/bias/current` persist immutable rules-based predictions with versioned evidence.
- Migration `011_bias_predictions.sql` applied.
- Phase 4 explanation slice added: `LLMProvider` and `GeminiBiasExplainer` accept only deterministic bias evidence and validate structured explanation output; 72 tests pass.
- Phase 4 explanation persistence slice added: migration `012_bias_explanations.sql`, bounded `/api/v1/bias/history`, and linked `/api/v1/bias/{id}/explain` storage are implemented.
- Migration `012_bias_explanations.sql` applied and verified; live deterministic bias generation and Gemini explanation smoke tests returned HTTP 200 with persisted IDs.
- Phase 4 acceptance completed: deterministic bias, immutable persistence, evidence fields, history, catalyst guardrail, and evidence-constrained Gemini explanation are implemented and smoke-tested.
- Phase 5 analogue slice added: reproducible StandardScaler-style Euclidean/cosine ranking with historical date/availability filtering, missing-feature exclusion, and 30m outcome aggregation foundation.
- Phase 5 persistence/API slice added: migration `013_analogue_vectors.sql`, `SupabaseAnalogueRepository`, and `POST /api/v1/regimes/similar` expose bounded point-in-time analogue retrieval.
- Phase 5 vector population slice added: `jobs/populate_analogue_vectors.py` populated 171 stored 2026 session vectors using only pre-session fields; live similar-regimes verification returned ranked matches.
- Phase 5 outcome slice added: deterministic session outcomes now calculate available 30m/60m returns, open-to-close return, ONH/ONL-first labels, and a trend-day baseline; analogue responses aggregate those outcomes without changing the point-in-time feature vector.
- Phase 5 bias integration slice added: optional analogue bull-rate and return summaries enrich deterministic bias evidence/cases without changing Phase 4 score weights or catalyst guardrails.
- Phase 5 end-to-end API slice added: `POST /bias/generate` can retrieve point-in-time analogues, feed their aggregate summary into evidence, and return ranked matches with the prediction.
- Phase 5 dashboard slice added: `/regime` provides a responsive, accessible historical-regime query form and results table backed by `POST /regimes/similar`.
- Phase 5 market-context slice added: `GET /market/nq/analogue-features` exposes the backend-calculated analogue vector, and `/regime` can load it before searching.
- Phase 5 outcome visualization slice added: `/regime` displays historical 30m/60m/open-to-close ranges and ONH/ONL/trend-day read-through metrics; strategy-specific performance remains deferred to Phase 7.
- Phase 5 repository verification completed: hosted Supabase contains 171 analogue vectors and all 171 have outcome payloads; latest stored session is `2026-09-02`.
- Phase 6 ontology foundation added: Neo4j constraints, separate regime dimensions, and idempotent semantic session-to-regime synchronization are defined; raw candles remain in Supabase.
- Phase 6 classification slice added: deterministic v0 regime dimensions are calculated in `graph/regimes.py` with isolated, tested thresholds and neutral defaults for missing macro/catalyst context.
- Phase 6 synchronization slice added: `jobs/sync_graph.py` initializes Neo4j constraints and synchronizes stored sessions into semantic regime relationships; live verification found 171 `MarketSession` nodes and 12 `MarketRegime` nodes.
- Phase 6 source-record slice added: `jobs/sync_graph_sources.py` synchronizes normalized news, macro calendar events, and bias predictions; live verification found 23 `NewsEvent`, 13 `MacroEvent`, and 2 `Company` nodes. No predictions existed in the selected historical window.
- Phase 6 traversal slice added: `GET /knowledge/regimes` returns bounded graph-backed sessions filtered by independent ontology dimensions; live verification returned 20 `GAP_UP` sessions.
- Phase 6 completion slice added: prediction-to-outcome relationship and strategy-evidence traversal contracts are implemented; strategy results remain empty until Phase 7 strategy memory creates records.
- Phase 7 strategy foundation added: structured strategy model/validation, Supabase repository, migration `014_strategies.sql`, and `POST/GET /strategies` are implemented.
- Phase 7 CRUD slice added: `GET/PATCH/DELETE /strategies/{id}` now support retrieval, replacement, and soft deactivation; migration `014` is applied.
- Phase 7 setup-detection slice added: supported structured conditions are detected from stored regular-session bars and persisted idempotently by `jobs/detect_setups.py`; migration `015_strategy_setups.sql` is applied. The active PB strategy currently fails closed because its full multi-timeframe conditions are not yet wired into the detector.
- Phase 7 performance foundation added: deterministic statistics calculation covers sample size, win rate, return summaries, expectancy, optional MFE/MAE, and Sharpe-like ratio; unavailable fields remain unset.
- Phase 7 outcome slice added: strategy outcome model/repository, migration `016_strategy_outcomes.sql`, and `GET /strategies/{id}/performance` are implemented; migration `016` is applied.
- Phase 7 strategy dashboard slice added: `/strategies` provides structured strategy creation, saved-strategy selection, rule detail, and outcome-backed performance metrics with explicit empty states; migration `016` is applied and the outcome table is reachable.
- Live strategy memory now contains one active `PB Blake / ICT-style Intraday Setup` record with six required HTF/liquidity/LTF conditions, four optional confirmations, and explicit no-trade invalidations. The current detector fails closed on its unsupported conditions until full multi-timeframe logic is implemented.
- PB Blake / ICT deterministic evaluator added at `apps/api/src/nqmate_api/strategies/pb_blake.py`: enforces HTF context, liquidity-before-inversion sequence, point-in-time filtering, highest valid LTF inversion selection, and conservative `VALID`/`DEVELOPING`/`NO_SETUP` outcomes. It is wired to the explicit historical assessment endpoint; no live feed is required.
- PB Blake historical input slice added at `apps/api/src/nqmate_api/strategies/pb_blake_data.py`: detects three-bar FVGs and post-liquidity close-through inversions from point-in-time historical bars for backtesting; HTF context and trade levels remain explicit inputs.
- PB assessment API slice added at `POST /api/v1/strategies/{id}/assess`: evaluates normalized historical evidence, returns `VALID`/`DEVELOPING`/`NO_SETUP`, and persists only valid setup occurrences.
- Strategy outcome regime support added with migration `017_strategy_outcome_regime.sql`; migration 017 has been applied to Supabase and performance now reports best/worst regime from stored regime-labeled outcomes.
- Phase 8 baseline slice added at `apps/api/src/nqmate_api/ml/`: majority-class, always-long, overnight-direction, and dependency-light logistic-regression baselines; point-in-time row filtering and chronological walk-forward splits are tested. This is a benchmark foundation, not final ML acceptance.
- Phase 8 dataset slice added at `apps/api/src/nqmate_api/ml/dataset.py`: exact-timestamp forward direction targets, missing-horizon exclusion, versioned feature matrices, and feature-availability leakage checks are tested.
- Phase 8 evaluation slice added at `apps/api/src/nqmate_api/ml/metrics.py`: deterministic accuracy, precision, recall, Brier, log-loss, and ROC-AUC metrics plus chronological out-of-sample comparison of the four baseline models are tested.
- Phase 8 metadata slice added at `apps/api/src/nqmate_api/ml/`: dataset/model records, Supabase repository, and migration `018_ml_metadata.sql` are implemented; dataset versions are idempotent and model artifacts are insert-only. Migration 018 is applied.
- Phase 8 historical baseline runner added at `jobs/evaluate_ml_baselines.py`: stored analogue vectors/outcomes can be converted into 30-minute direction rows, evaluated with chronological folds, and registered as inactive baseline metadata records. It requires at least the configured training-window size of complete rows.
- Phase 8 baseline run completed against stored 2026 history: 151 out-of-sample rows and four registered inactive models. Accuracy was majority 52.98%, always-long 52.98%, overnight-direction 49.67%, and logistic 49.01%; logistic did not beat the simple baseline.
- Phase 8 XGBoost challenger added with optional `xgboost` and `scikit-learn` dependencies; the first walk-forward run scored 49.67% accuracy on the same 151 rows, below the majority baseline, and was registered inactive rather than promoted.
- Phase 8 multi-horizon runner added: `jobs/evaluate_ml_baselines.py` now creates horizon-specific metadata for stored outcomes. The first 60-minute run covered 151 rows: always-long 56.29%, majority 54.97%, XGBoost 54.30%, and logistic 44.37%; no challenger was promoted.
- Phase 8 three-way boosting comparison completed for 30m and 60m: scikit-learn Gradient Boosting is the current best candidate for 60m at 58.94% versus 56.29% always-long; XGBoost and LightGBM did not beat it. No model is active until multiple-window validation and calibration pass.
- Phase 8 target-contract slice added at `apps/api/src/nqmate_api/ml/targets.py`: explicit 5m/15m/30m/60m/120m/240m/close direction target names and exact-time target matrix support are tested; missing future bars are excluded.
- Phase 8 calibration slice added at `apps/api/src/nqmate_api/ml/calibration.py`: expected calibration error, multiple expanding walk-forward windows, and accuracy/Brier promotion gating are tested. The current 60m Gradient Boosting candidate remains inactive pending these checks.
- Phase 8 multi-window runner added at `jobs/evaluate_ml_windows.py`: configurable expanding-window validation of the stored 60m target now compares all boosting implementations without activating or overwriting registry models.
- Phase 8 multi-window validation completed for 60m with train sizes 20/40/60 and 10-row tests: scikit-learn Gradient Boosting led accuracy in every window (59.44%/61.80%/63.92%), but its Brier scores remained worse than the majority baseline, so it was not promoted.
- Phase 8 calibration metrics added to model evaluation: stored metric payloads now include expected calibration error. General directional models remain separate from PB strategy evaluation; no PB-specific ML model is active.
- Phase 8 historical outcomes expanded: analogue vectors now store 5m/15m/120m/240m returns when exact bars exist. Verification found 95 sessions with 5m/15m outcomes, 2 with 120m, and 0 with 240m. Initial 5m/15m challenger runs were registered inactive; no model was promoted.
- Phase 8 candle-horizon slice added: `jobs/populate_market_timeframes.py` derives and persists canonical `5m`, `15m`, `1h`, `2h`, `4h`, and `1d` candles from stored 1-minute bars; `2h`/`4h` represent 120m/240m horizons and the API accepts those aliases.
- Historical candle population completed for 2026-01-01 through 2026-09-02: Supabase verification found 47,258 `5m`, 15,755 `15m`, 3,940 `1h`, 2,056 `2h`, 1,066 `4h`, and 208 `1d` bars. The source remains the canonical stored 1-minute history.
- Horizon evaluations rerun after candle population: 5m and 15m each produced 151 out-of-sample rows. At 5m, XGBoost and LightGBM reached 53.64% accuracy but remain inactive; at 15m, the majority baseline led at 56.29% and all challengers remain inactive.
- Versioned dataset-catalog slice added: `jobs/register_ml_datasets.py` registered 5m/15m/30m/60m/120m/close directional datasets from real analogue outcomes; 120m currently has 3 rows and 240m is omitted because no valid rows exist. Absent horizons are skipped rather than imputed.
- Market candle retrieval corrected: the bars API now prefers persisted requested-timeframe rows and aggregates only canonical 1-minute rows, preventing double aggregation after derived candles are stored.
- Phase 8 implementation closed: the multi-window runner now accepts any directional outcome. 5m, 15m, 30m, and 60m checks found no candidate satisfying both out-of-sample improvement and the Brier-score gate, so no model was activated.
- Phase 9 reconstruction slice added: migration `019_prediction_reconstruction.sql` and bias repository persistence now retain the exact deterministic input snapshot with model/feature versions; migration 019 is applied.
- Phase 9 outcome-attachment slice added: migration `020_prediction_outcomes.sql`, deterministic directional correctness logic, repository persistence, and `jobs/attach_prediction_outcomes.py` are implemented; migration 020 is applied and requires an explicit prediction ID plus historical session date.
- Phase 9 diagnostics slice added: deterministic per-horizon outcome summaries and `GET /api/v1/bias/{prediction_id}/evaluation` expose coverage, accuracy, average return, and win rate without mutating predictions.
- Phase 9 calibration slice added: `GET /api/v1/bias/evaluation` reports bounded confidence-bin calibration from attached directional outcomes; neutral/unscored outcomes are excluded.
- Phase 9 drift slice added: `feature_drift` and `GET /api/v1/bias/drift` compare older/newer numeric prediction snapshots and report stable, watch, or drift states without mutating predictions.
- Phase 9 champion/challenger slice added: `champion_challenger_report` and `jobs/report_model_comparisons.py` provide read-only baseline-gated registry comparisons; no model is auto-activated.
- Champion/challenger reporting corrected to prefer majority over always-long and exclude duplicate/simple baselines from challenger output; the corrected 5m report found no eligible challenger because Brier scores failed the gate.
- Phase 9 registry visibility slice added: bounded `GET /api/v1/ml/models` exposes stored model metadata and active state with optional target filtering; it is read-only.
- Phase 9 comparison API slice added: read-only `GET /api/v1/ml/models/comparison` exposes the same gated champion/challenger report as the CLI job.
- Phase 9 grouped-diagnostics slice added: `grouped_outcome_metrics` reports accuracy and average return by explicit regime/event labels and skips missing labels.
- Phase 9 reconstruction endpoint added: read-only `GET /api/v1/bias/{prediction_id}/reconstruction` returns the stored input snapshot, result, versions, creation time, and attached outcomes for auditability.
- Phase 9 observability slice added: bounded `GET /api/v1/bias/observability` reports prediction/outcome coverage, reconstruction completeness, and model/feature version sets without mutating data.
- Phase 9 automatic-attachment slice added: migration `021_prediction_session_date.sql` stores explicit session dates on context-linked predictions, and `jobs/attach_completed_prediction_outcomes.py` attaches available outcomes without date guessing; migration 021 is applied. The first run attached 0 outcomes because existing predictions predate session-date persistence and were safely skipped.
- Phase 9 dashboard slice added: responsive `/evaluation` page displays coverage, calibration, drift, model registry, and gated promotion evidence with explicit loading/error/empty states; Next.js production build passes.
- Primary market dashboard slice added: `/dashboard` displays completed-session 5-minute candles with PDH/PDL overlays, ONH/ONL/midpoint liquidity levels, deterministic session metrics, stored bias evidence, and cached high-impact news; it is historical and has no execution controls.
- Dashboard context slice added: `/dashboard` now reads stored 15m, 4H, and daily candles and displays their deterministic momentum read-through alongside the completed-session chart; no live data is implied.
- Dashboard level-overlay slice added: the historical 5m chart now draws stored ONH/ONL, overnight midpoint, and VWAP overlays in addition to PDH/PDL.
- Dashboard session-selection slice added: `/dashboard` now reloads stored session, candle, level, feature, bias, and news views when a completed session date is selected.
- PB historical assessment slice added: `GET /strategies/{id}/assess-session` builds point-in-time HTF/liquidity/LTF evidence from stored candles, and `/dashboard` displays deterministic PB status, trade levels, risk/reward, and missing evidence without forcing a setup.
- Historical evaluation replay duplicate coverage expanded to the full stored prediction history, allowing larger session backfills without creating duplicate session-linked predictions on later runs.
- Phase 9 evaluation-report bound expanded to 1,000 predictions; the evaluation dashboard now requests the complete stored historical replay sample rather than the previous 100-record view.
- Phase 9 success-rate slice added: `/bias/evaluation` now returns overall and per-horizon directional accuracy/return summaries, and `/evaluation` displays them with scored-sample counts.
- Phase 9 attachment job rerun from `apps/api`: 5 realized outcomes are now attached idempotently. Directional calibration remains empty because the linked prediction is neutral, and neutral predictions are intentionally excluded from scored directional outcomes.
- Phase 9 daily attachment automation added: `jobs/attach_completed_prediction_outcomes_daily.py` and `ops/com.nqmate.prediction-outcomes-daily.plist` schedule the existing idempotent outcome job for 4:15 PM Eastern; the LaunchAgent is installed and loaded on the current Mac.
- Phase 9 evaluation replay added: `jobs/generate_historical_bias_predictions.py` creates explicit session-linked evaluation predictions from stored pre-session overnight/gap inputs while keeping unavailable context neutral; it is separate from production bias generation.

## In Progress

Phase 5 acceptance is complete. Phase 6 implementation is complete for the available source boundaries, semantic relationships, deterministic regime classification, bounded graph retrieval, and outcome/strategy traversal contracts. Phase 7 implementation is complete for structured strategy CRUD, setup detection, performance calculation, regime-conditioned best/worst statistics, outcome persistence, the strategy dashboard, historical FVG/inversion detection, and the PB assessment endpoint; migrations `014`–`017` are applied and live strategy read verification found one active strategy. Phase 8 implementation is complete with leakage-aware baselines, multi-horizon targets, boosting comparisons, calibration metrics, dataset/model metadata, historical candle horizons, and multi-window validation; no model passed the promotion gate. Phase 9 implementation is complete with reconstruction, attachment, scored outcomes, calibration, drift, registry/comparison reporting, observability, replay tooling, scheduled attachment, and evaluation UI. Current replay evidence contains 172 predictions, 521 attached outcomes, and 361 scored directional outcomes; overall directional accuracy is 43.8%, and calibration remains weak, so no model is promoted. The literal Phase 6 strategy-evidence query remains empty until strategy performance relationships exist. The BLS calendar feed requires a network change or manual official-feed retrieval before scheduled release ingestion can run live. The primary market dashboard is available at `/dashboard` for completed historical sessions; it is not a live chart. September 3 remains incomplete/current until its session closes.

## Next

1. Collect more point-in-time predictions before interpreting calibration or drift
2. Add dashboard HTF/15m/entry visuals only when backed by available deterministic API data

## Important Decisions

- Python owns deterministic market calculations.
- Next.js is primarily the frontend; FastAPI is the application/data/ML backend.
- PostgreSQL/Supabase stores numerical and relational truth; Neo4j stores semantic relationships, not raw candles.
- Start with minute bars.
- Market providers must be swappable.
- The LLM explains supplied evidence rather than inventing market statistics.
- No automated trade execution in V1.
- Prevent look-ahead bias with point-in-time data.
- Deep learning is post-V1; XGBoost/LightGBM is the first serious ML model after the baseline.
- V1 is backtest and completed-session research focused; a real-time intraday NQ feed is not required. Do not add live-bar infrastructure unless the scope is explicitly changed.

## Blockers

None.

## Last Updated

2026-09-05
