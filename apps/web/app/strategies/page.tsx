"use client";

import { FormEvent, useEffect, useState } from "react";

type Strategy = { id: string; name: string; description?: string; required_conditions?: string[]; confirmation_conditions?: string[]; invalidation_conditions?: string[]; entry_logic: string; target_logic: string; stop_logic: string; active: boolean };
type Performance = { sample_size: number; win_rate: number; mean_return: number | null; expectancy: number | null; mfe_mean: number | null; mae_mean: number | null; sharpe_like: number | null };
const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

function percent(value: number | null) { return value == null ? "—" : `${(value * 100).toFixed(2)}%`; }

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selected, setSelected] = useState<Strategy | null>(null);
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [name, setName] = useState("");
  const [entry, setEntry] = useState("");
  const [target, setTarget] = useState("");
  const [stop, setStop] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadStrategies() {
    try {
      const response = await fetch(`${apiBase}/strategies`);
      if (!response.ok) throw new Error(`Could not load strategies (${response.status})`);
      const payload = (await response.json()) as { strategies: Strategy[] };
      setStrategies(payload.strategies);
      if (payload.strategies.length && !selected) setSelected(payload.strategies[0]);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not load strategies"); }
    finally { setLoading(false); }
  }

  useEffect(() => { void loadStrategies(); }, []);

  useEffect(() => {
    if (!selected) { setPerformance(null); return; }
    void fetch(`${apiBase}/strategies/${selected.id}/performance`).then(async (response) => {
      if (!response.ok) throw new Error(`Could not load performance (${response.status})`);
      setPerformance((await response.json()).statistics as Performance);
    }).catch((caught) => setError(caught instanceof Error ? caught.message : "Could not load performance"));
  }, [selected]);

  async function createStrategy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSaving(true); setError(null);
    try {
      const response = await fetch(`${apiBase}/strategies`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name, entryLogic: entry, targetLogic: target, stopLogic: stop }) });
      if (!response.ok) throw new Error(`Could not save strategy (${response.status})`);
      const created = (await response.json()) as Strategy;
      setStrategies((current) => [created, ...current]); setSelected(created); setName(""); setEntry(""); setTarget(""); setStop("");
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not save strategy"); }
    finally { setSaving(false); }
  }

  return <main className="shell"><header className="page-header"><div><p className="eyebrow">NQMATE / MEMORY</p><h1>Strategy memory</h1><p className="subtitle">Save structured rules and measure them only against completed outcomes.</p></div><a className="quiet-link" href="/">Back to overview</a></header>
    {error && <p className="state error" role="alert">{error}. Check that the FastAPI server is running.</p>}
    <div className="strategy-layout"><section className="query-panel" aria-labelledby="saved-title"><div className="section-heading"><div><p className="eyebrow">SAVED RULES / {strategies.length}</p><h2 id="saved-title">Strategies</h2></div></div>{loading ? <div className="state" role="status">Loading strategies…</div> : strategies.length === 0 ? <div className="state"><strong>No strategies saved.</strong><span>Create a structured rule set to begin recording setups.</span></div> : <div className="strategy-list">{strategies.map((strategy) => <button className={`strategy-item ${selected?.id === strategy.id ? "selected" : ""}`} key={strategy.id} onClick={() => setSelected(strategy)}><span>{strategy.name}</span><small>{strategy.active ? "ACTIVE" : "INACTIVE"}</small></button>)}</div>}</section>
      <section className="query-panel" aria-labelledby="create-title"><p className="eyebrow">CREATE</p><h2 id="create-title">New strategy</h2><form onSubmit={createStrategy} className="strategy-form"><label>Name<input value={name} onChange={(event) => setName(event.target.value)} required maxLength={200} /></label><label>Entry logic<input value={entry} onChange={(event) => setEntry(event.target.value)} required maxLength={2000} /></label><label>Target logic<input value={target} onChange={(event) => setTarget(event.target.value)} required maxLength={2000} /></label><label>Stop logic<input value={stop} onChange={(event) => setStop(event.target.value)} required maxLength={2000} /></label><button className="primary-button" disabled={saving}>{saving ? "Saving…" : "Save strategy"}</button></form></section></div>
    {selected && <section className="query-panel detail-panel" aria-labelledby="detail-title"><div className="section-heading"><div><p className="eyebrow">PERFORMANCE</p><h2 id="detail-title">{selected.name}</h2></div><span className="badge">{selected.active ? "ACTIVE" : "INACTIVE"}</span></div><div className="metric-grid"><div><span>Sample size</span><strong>{performance?.sample_size ?? "—"}</strong></div><div><span>Win rate</span><strong>{performance ? percent(performance.win_rate) : "—"}</strong></div><div><span>Mean return</span><strong>{performance ? percent(performance.mean_return) : "—"}</strong></div><div><span>Expectancy</span><strong>{performance ? percent(performance.expectancy) : "—"}</strong></div></div><div className="rule-copy"><p><strong>Entry:</strong> {selected.entry_logic}</p><p><strong>Target:</strong> {selected.target_logic}</p><p><strong>Stop:</strong> {selected.stop_logic}</p></div><p className="footnote">Statistics use completed outcomes only. A zero or missing sample is not evidence of strategy quality.</p></section>}
  </main>;
}
