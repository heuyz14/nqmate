"use client";

import { useEffect, useState } from "react";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type Model = { name: string; target: string; algorithm: string; active: boolean; metrics?: { accuracy?: number; brier_score?: number } };
type CalibrationBin = { lower: number; upper: number; sample_size: number; mean_confidence: number; observed_accuracy: number; calibration_gap: number };
type DashboardData = {
  models: Model[];
  evaluation: { prediction_count: number; outcome_count: number; scored_outcome_count?: number; accuracy?: number; evaluated_size?: number; horizons?: Record<string, { sample_size: number; evaluated_size: number; accuracy: number | null; average_return: number | null; win_rate: number | null }>; confidence_calibration: CalibrationBin[] };
  drift: { prediction_count: number; features: Record<string, { score: number; status: string; reference_mean: number; current_mean: number }> };
  comparisons: Record<string, Array<{ name: string; algorithm: string; eligible: boolean; accuracy?: number; brier_score?: number }>>;
};

function percent(value?: number | null) { return value == null ? "—" : `${(value * 100).toFixed(1)}%`; }

export default function EvaluationPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [models, evaluation, drift, comparisons] = await Promise.all([
          fetch(`${apiBase}/ml/models`).then((response) => response.json()),
          fetch(`${apiBase}/bias/evaluation?limit=1000`).then((response) => response.json()),
          fetch(`${apiBase}/bias/drift?limit=1000`).then((response) => response.json()),
          fetch(`${apiBase}/ml/models/comparison`).then((response) => response.json()),
        ]);
        setData({ models: models.models ?? [], evaluation, drift, comparisons: comparisons.comparisons ?? {} });
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Could not load evaluation data");
      }
    }
    void load();
  }, []);

  return <main className="shell">
    <header className="page-header"><div><p className="eyebrow">NQMATE / PHASE 9</p><h1>Evaluation desk</h1><p className="subtitle">Audit prediction quality, data drift, and model promotion evidence from stored results.</p></div><a className="quiet-link" href="/">Back to overview</a></header>
    {error && <div className="state error" role="alert"><strong>Evaluation data unavailable.</strong><span>{error}. Check that the FastAPI server is running.</span></div>}
    {!data && !error && <div className="state" role="status" aria-busy="true"><strong>Loading evaluation data…</strong><span>Reading bounded registry and diagnostics reports.</span></div>}
    {data && <>
      <section className="metric-grid" aria-label="Evaluation coverage"><div><span>Registered models</span><strong>{data.models.length}</strong></div><div><span>Predictions</span><strong>{data.evaluation.prediction_count}</strong></div><div><span>Attached outcomes</span><strong>{data.evaluation.outcome_count}</strong></div><div><span>Scored outcomes</span><strong>{data.evaluation.scored_outcome_count ?? 0}</strong></div><div><span>Drift fields</span><strong>{Object.keys(data.drift.features).length}</strong></div></section>
      <section className="query-panel horizon-panel" aria-labelledby="horizon-title"><div className="section-heading"><div><p className="eyebrow">SUCCESS RATES</p><h2 id="horizon-title">Directional accuracy by horizon</h2></div><span className="badge">{data.evaluation.evaluated_size ?? 0} scored</span></div><div className="metric-grid horizon-grid"><div><span>Overall accuracy</span><strong>{percent(data.evaluation.accuracy)}</strong></div>{Object.entries(data.evaluation.horizons ?? {}).map(([horizon, item]) => <div key={horizon}><span>{horizon.replace("return_", "").replace("m", " min")}</span><strong>{percent(item.accuracy)}</strong><small>{item.evaluated_size} scored · positive return {percent(item.win_rate)} · avg return {percent(item.average_return)}</small></div>)}</div></section>
      <div className="insight-grid">
        <section className="insight-panel" aria-labelledby="calibration-title"><p className="eyebrow">CALIBRATION</p><h2 id="calibration-title">Confidence vs observed accuracy</h2>{data.evaluation.confidence_calibration.length === 0 ? <div className="state"><strong>No scored outcomes yet.</strong><span>Attach realized outcomes before interpreting calibration.</span></div> : <div className="calibration-list">{data.evaluation.confidence_calibration.map((bin) => <div className="calibration-row" key={`${bin.lower}-${bin.upper}`}><div><span>{percent(bin.lower)}–{percent(bin.upper)}</span><strong>{bin.sample_size} samples</strong></div><div className="calibration-track"><span style={{ width: `${Math.min(100, bin.mean_confidence * 100)}%` }} /><i style={{ left: `${Math.min(100, bin.observed_accuracy * 100)}%` }} /></div><small>Predicted {percent(bin.mean_confidence)} · observed {percent(bin.observed_accuracy)} · gap {percent(bin.calibration_gap)}</small></div>)}</div>}</section>
        <section className="insight-panel" aria-labelledby="drift-title"><p className="eyebrow">DRIFT</p><h2 id="drift-title">Input stability</h2>{Object.keys(data.drift.features).length === 0 ? <div className="state"><strong>Not enough snapshots.</strong><span>At least four reconstructed predictions are needed.</span></div> : <div className="drift-list">{Object.entries(data.drift.features).map(([name, item]) => <div className="drift-row" key={name}><div><span>{name}</span><strong>{item.status}</strong></div><small>{item.reference_mean.toFixed(3)} reference → {item.current_mean.toFixed(3)} current · score {item.score.toFixed(2)}</small></div>)}</div>}</section>
      </div>
      <section className="query-panel" aria-labelledby="models-title"><div className="section-heading"><div><p className="eyebrow">REGISTRY</p><h2 id="models-title">Models and promotion evidence</h2></div><span className="badge">Manual activation only</span></div><div className="table-wrap"><table><caption className="sr-only">Registered models and gated comparisons</caption><thead><tr><th scope="col">Target</th><th scope="col">Model</th><th scope="col">Algorithm</th><th scope="col">Accuracy</th><th scope="col">Brier</th><th scope="col">Gate</th><th scope="col">State</th></tr></thead><tbody>{data.models.map((model) => { const comparison = data.comparisons[model.target]?.find((item) => item.name === model.name); return <tr key={`${model.target}-${model.name}`}><td>{model.target}</td><td className="session-cell">{model.name}</td><td>{model.algorithm}</td><td>{percent(model.metrics?.accuracy)}</td><td>{model.metrics?.brier_score?.toFixed(3) ?? "—"}</td><td>{comparison ? comparison.eligible ? "ELIGIBLE" : "INACTIVE" : "BASELINE"}</td><td>{model.active ? "ACTIVE" : "INACTIVE"}</td></tr>; })}</tbody></table></div>{data.models.length === 0 && <div className="state"><strong>No models registered.</strong><span>Run the Phase 8 evaluation jobs before reviewing promotion evidence.</span></div>}</section>
    </>}
  </main>;
}
